"""
services.py - School, class, section and people management
==========================================================

Owner: Rajneesh Kumar (tasks R-02, R-03, R-04)

Rules kept here (not in views):
    * School rename and capacity change show an overwrite warning first (views).
    * Only the Super Admin changes capacity; capacity cannot go below current students.
    * New sections must fit the plan's section limit.
    * A student is only added when the section has room (SectionFullError).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.services import UserService
from apps.accounts.validators import validate_person_name
from apps.core.exceptions import AccessDeniedError, SectionFullError, ValidationError
from apps.core.models import SystemSettings
from apps.core.services import AuditService

from .models import School, SchoolClass, Section, StudentProfile

User = get_user_model()


class SchoolService:
    """Create and change schools, classes and sections."""

    @transaction.atomic
    def create_school(self, code: str, name: str, by=None, **extra) -> School:
        code = School.clean_code(code)
        if School.objects.filter(code=code).exists():
            raise ValidationError(f"School code {code} is already used.")
        if len((name or "").strip()) < 3:
            raise ValidationError("School name must have at least 3 characters.")
        school = School.objects.create(code=code, name=name.strip(), **extra)
        from apps.licensing.services import LicenseService  # pylint: disable=import-outside-toplevel
        LicenseService().start_trial(school)
        AuditService.log(by, "school_created", code, new=name)
        return school

    @staticmethod
    def rename(school: School, new_name: str, by=None) -> tuple[str, str]:
        new_name = (new_name or "").strip()
        if len(new_name) < 3:
            raise ValidationError("School name must have at least 3 characters.")
        old = school.name
        school.name = new_name
        school.save(update_fields=["name"])
        AuditService.log(by, "school_renamed", school.code, old, new_name)
        return old, new_name

    @staticmethod
    def set_active(school: School, active: bool, by=None) -> None:
        school.is_active = active
        school.save(update_fields=["is_active"])
        AuditService.log(by, "school_status", school.code, not active, active)

    @staticmethod
    def add_class(school: School, name: str, year_level: int, by=None) -> SchoolClass:
        if not (name or "").strip():
            raise ValidationError("Please give the class a name, e.g. Year 7.")
        if SchoolClass.objects.filter(school=school, name__iexact=name.strip()).exists():
            raise ValidationError("A class with this name already exists.")
        cls = SchoolClass.objects.create(school=school, name=name.strip(), year_level=year_level)
        AuditService.log(by, "class_created", school.code, new=name)
        return cls

    @staticmethod
    def add_section(school_class: SchoolClass, name: str, by=None) -> Section:
        from apps.licensing.services import LicenseService  # pylint: disable=import-outside-toplevel
        LicenseService().check_section_limit(school_class.school)
        if not (name or "").strip():
            raise ValidationError("Please give the section a name, e.g. 7A.")
        if Section.objects.filter(school_class=school_class, name__iexact=name.strip()).exists():
            raise ValidationError("A section with this name already exists in this class.")
        capacity = SystemSettings.load().default_section_capacity
        section = Section.objects.create(school_class=school_class, name=name.strip(), capacity=capacity)
        AuditService.log(by, "section_created", school_class.school.code, new=f"{name} (capacity {capacity})")
        return section

    @staticmethod
    def preview_capacity(section: Section, raw) -> tuple[int, int]:
        try:
            new = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Capacity must be a whole number.") from exc
        if not 1 <= new <= 60:
            raise ValidationError("Capacity must be between 1 and 60.")
        if new < section.student_count:
            raise ValidationError(f"Section {section.name} already has {section.student_count} students. "
                                  "Move some students first.")
        return section.capacity, new

    def change_capacity(self, section: Section, raw, by=None) -> tuple[int, int]:
        if not getattr(by, "is_super_admin", False):
            raise AccessDeniedError("Only the Super Admin can change a section's capacity.")
        old, new = self.preview_capacity(section, raw)
        section.capacity = new
        section.save(update_fields=["capacity"])
        AuditService.log(by, "section_capacity", f"{section.school.code} {section.name}", old, new)
        return old, new


@dataclass
class ImportResult:
    """What happened during a CSV import."""

    added: list = field(default_factory=list)
    errors: list = field(default_factory=list)   # (row number, message)


class PeopleService:
    """Add and manage students and teachers in a school."""

    def __init__(self):
        self.users = UserService()

    @transaction.atomic
    def add_student(self, school: School, *, first_name, last_name, section: Section, password,
                    family_consent=False, parent_name="", parent_email="", parent_opt_in=False, by=None):
        """Create a student login + profile and put them in a section (if there is room)."""
        if section.school.pk != school.pk:
            raise AccessDeniedError("That section is not in this school.")
        section.check_room()
        first_name, last_name = validate_person_name(first_name), validate_person_name(last_name)
        user = self.users.create_user(first_name=first_name, last_name=last_name, role="student", school=school,
                                      password=password, by=by)
        profile = user.student_profile
        profile.family_consent = family_consent
        profile.parent_name, profile.parent_email, profile.parent_opt_in = parent_name, parent_email, parent_opt_in
        section.add_student(profile)
        return user

    def add_teacher(self, school: School, *, first_name, last_name, email, password, by=None):
        return self.users.create_user(first_name=validate_person_name(first_name),
                                      last_name=validate_person_name(last_name), role="teacher",
                                      school=school, email=email, password=password, by=by)

    @staticmethod
    def move_student(profile: StudentProfile, section: Section, by=None) -> None:
        if profile.user.school_id != section.school.pk:
            raise AccessDeniedError("You can only move students inside the same school.")
        if profile.section_id == section.pk:
            return
        section.check_room()
        old = str(profile.section)
        section.add_student(profile)
        AuditService.log(by, "student_moved", profile.user.username, old, str(section))

    def import_csv(self, school: School, file_obj, by=None, commit: bool = True) -> ImportResult:
        """Import students from CSV: first_name,last_name,section,password,family_consent,parent_email.

        ``commit=False`` only checks the rows (preview)."""
        result = ImportResult()
        try:
            text = file_obj.read().decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValidationError("The CSV file must be saved as UTF-8.") from exc
        reader = csv.DictReader(io.StringIO(text))
        needed = {"first_name", "last_name", "section", "password"}
        if not reader.fieldnames or not needed.issubset({f.strip() for f in reader.fieldnames}):
            raise ValidationError("CSV columns must include: first_name, last_name, section, password.")
        sections = {s.name.lower(): s for s in Section.objects.filter(school_class__school=school)}
        planned: dict[int, int] = {}
        for number, row in enumerate(reader, start=2):
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            section = sections.get(row["section"].lower())
            try:
                if section is None:
                    raise ValidationError(f"Section '{row['section']}' does not exist.")
                if section.student_count + planned.get(section.pk, 0) + 1 > section.capacity:
                    raise SectionFullError(f"Section {section.name} would be over its limit ({section.capacity}).")
                validate_person_name(row["first_name"])
                validate_person_name(row["last_name"])
                if len(row["password"]) < 8:
                    raise ValidationError("Password must have at least 8 characters.")
                if commit:
                    user = self.add_student(school, first_name=row["first_name"], last_name=row["last_name"],
                                            section=section, password=row["password"],
                                            family_consent=row.get("family_consent", "").lower() in {"yes", "1", "true"},
                                            parent_email=row.get("parent_email", ""), by=by)
                    result.added.append(user.username)
                else:
                    result.added.append(f"{row['first_name']} {row['last_name']}")
                planned[section.pk] = planned.get(section.pk, 0) + 1
            except Exception as exc:  # pylint: disable=broad-except
                result.errors.append((number, getattr(exc, "message", None) or "; ".join(getattr(exc, "messages", [str(exc)]))))
        if commit:
            AuditService.log(by, "students_imported", school.code, new=f"{len(result.added)} added, {len(result.errors)} errors")
        return result

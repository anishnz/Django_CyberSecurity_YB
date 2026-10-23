"""
models.py - Schools, classes, sections and student profiles
===========================================================

Owner: Rajneesh Kumar (task R-01)

Concepts:
    * Relationships: School 1─* SchoolClass 1─* Section 1─* StudentProfile.
    * Encapsulation: ``Section.add_student()`` is the only way to put a student in
      a section, and it refuses when the section is full (SectionFullError).
    * Database rules (constraints): capacity must be 1–60; school code unique.
"""

from __future__ import annotations

import re

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.exceptions import SectionFullError, ValidationError

CODE_RE = re.compile(r"^[A-Z0-9]{3,20}$")


class School(models.Model):
    """A school (kura) that uses CyberQuest."""

    REGIONS = [("northland", "Northland (Te Tai Tokerau)"), ("auckland", "Auckland (Tāmaki Makaurau)"),
               ("waikato", "Waikato"), ("bay_of_plenty", "Bay of Plenty (Te Moana-a-Toi)"),
               ("wellington", "Wellington (Te Whanganui-a-Tara)"), ("canterbury", "Canterbury (Waitaha)"),
               ("other", "Other")]

    code = models.CharField(max_length=20, unique=True, help_text="Capital letters and numbers, e.g. BRIGHTSTAR")
    name = models.CharField(max_length=120)
    region = models.CharField(max_length=30, choices=REGIONS, default="northland")
    address = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    logo = models.ImageField(upload_to="schools/logos/", blank=True)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def clean_code(code: str) -> str:
        """Check a school code: 3–20 capital letters or numbers."""
        code = (code or "").strip().upper()
        if not CODE_RE.match(code):
            raise ValidationError("School code must be 3–20 capital letters or numbers, e.g. BRIGHTSTAR.")
        return code

    @property
    def student_count(self) -> int:
        return StudentProfile.objects.filter(section__school_class__school=self).count()

    @property
    def section_count(self) -> int:
        return Section.objects.filter(school_class__school=self).count()


class SchoolClass(models.Model):
    """A class (akomanga), e.g. Year 7."""

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=60)
    year_level = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(15)])

    class Meta:
        ordering = ["year_level", "name"]
        constraints = [models.UniqueConstraint(fields=["school", "name"], name="unique_class_name_per_school")]

    def __str__(self) -> str:
        return f"{self.name} ({self.school.code})"


class Section(models.Model):
    """A group of students inside a class, e.g. 7A. Holds at most ``capacity`` students."""

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=40)
    capacity = models.PositiveSmallIntegerField(default=35, validators=[MinValueValidator(1), MaxValueValidator(60)])

    class Meta:
        ordering = ["school_class__year_level", "name"]
        constraints = [
            models.UniqueConstraint(fields=["school_class", "name"], name="unique_section_name_per_class"),
            models.CheckConstraint(condition=models.Q(capacity__gte=1) & models.Q(capacity__lte=60),
                                   name="section_capacity_1_to_60"),
        ]

    def __str__(self) -> str:
        return f"{self.name} – {self.school_class.name}"

    @property
    def school(self) -> School:
        return self.school_class.school

    @property
    def student_count(self) -> int:
        return self.students.count()

    @property
    def is_full(self) -> bool:
        return self.student_count >= self.capacity

    @property
    def label(self) -> str:
        """Size shown on screen, e.g. '28/35'."""
        return f"{self.student_count}/{self.capacity}"

    def check_room(self, extra: int = 1) -> None:
        """Raise SectionFullError if ``extra`` more students would not fit."""
        if self.student_count + extra > self.capacity:
            raise SectionFullError(
                f"Section {self.name} is full ({self.student_count}/{self.capacity}). "
                "Ask the Super Admin to raise the limit.")

    def add_student(self, profile: "StudentProfile") -> "StudentProfile":
        """Put a student in this section (only if there is room)."""
        self.check_room()
        profile.section = self
        profile.save()
        return profile


class StudentProfile(models.Model):
    """Extra details for a student: section, family consent, level and parent contact."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name="students")
    family_consent = models.BooleanField(default=False, help_text="Family (whānau) consent form received.")
    current_level = models.PositiveSmallIntegerField(default=1)
    parent_name = models.CharField(max_length=120, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_phone = models.CharField(max_length=30, blank=True)
    parent_opt_in = models.BooleanField(default=False, help_text="Parent agreed to receive emails and messages.")

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self) -> str:
        return f"{self.user} ({self.section})"

    @property
    def can_play(self) -> bool:
        """A student can study and sit quizzes only with family consent."""
        return self.family_consent

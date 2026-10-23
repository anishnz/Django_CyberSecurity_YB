"""test_schools.py - Schools, sections (35 limit), overwrite warnings, CSV import. Owners: Jihe Qi / Rajneesh Kumar."""
import io

import pytest

from apps.core.exceptions import AccessDeniedError, LicenseLimitError, SectionFullError
from apps.core.models import AuditLog
from apps.schools.models import School, Section
from apps.schools.services import PeopleService, SchoolService

pytestmark = pytest.mark.django_db


def _section(code, name):
    return Section.objects.get(school_class__school__code=code, name=name)


def test_us03_full_section_rejects_new_student():
    school = School.objects.get(code="BRIGHTSTAR")
    full = _section("BRIGHTSTAR", "7C")
    assert full.is_full and full.label == "35/35"
    with pytest.raises(SectionFullError):
        PeopleService().add_student(school, first_name="New", last_name="Kid", section=full, password="Kiaora2026")


def test_capacity_change_needs_warning_then_confirm(login):
    c = login("superadmin")
    s = _section("BRIGHTSTAR", "7C")
    r = c.post(f"/schools/sections/{s.pk}/capacity/", {"capacity": 40})
    assert r.status_code == 200 and b"Overwrite warning" in r.content
    s.refresh_from_db()
    assert s.capacity == 35                               # nothing saved yet
    c.post(f"/schools/sections/{s.pk}/capacity/", {"capacity": 40, "confirmed": "yes"})
    s.refresh_from_db()
    assert s.capacity == 40 and AuditLog.objects.filter(action="section_capacity").exists()


def test_capacity_cannot_go_below_students():
    s = _section("BRIGHTSTAR", "7C")
    from apps.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        SchoolService().preview_capacity(s, 10)


def test_only_super_admin_changes_capacity(user):
    with pytest.raises(AccessDeniedError):
        SchoolService().change_capacity(_section("BRIGHTSTAR", "7A"), 30, by=user("admin.brightstar"))


def test_rename_shows_old_and_new(login):
    c = login("superadmin")
    school = School.objects.get(code="KTMVALLEY")
    r = c.post(f"/schools/{school.pk}/rename/", {"name": "Kathmandu Valley School"})
    assert b"Kathmandu Valley Demo School" in r.content and b"Kathmandu Valley School" in r.content


def test_trial_plan_allows_one_section():
    kauri = School.objects.get(code="KAURICOAST")
    cls = SchoolService.add_class(kauri, "Year 5", 5)
    SchoolService.add_section(cls, "5A")
    with pytest.raises(LicenseLimitError):
        SchoolService.add_section(cls, "5B")


def test_csv_import_preview_then_import():
    school = School.objects.get(code="BRIGHTSTAR")
    data = ("first_name,last_name,section,password,family_consent,parent_email\n"
            "Aroha,Testing,7B,Kiaora2026x,yes,p@example.com\nBad<script>,Name,7B,Kiaora2026x,yes,\n"
            "Full,Section,7C,Kiaora2026x,yes,\n")
    preview = PeopleService().import_csv(school, io.BytesIO(data.encode()), commit=False)
    assert len(preview.added) == 1 and len(preview.errors) == 2
    result = PeopleService().import_csv(school, io.BytesIO(data.encode()), commit=True)
    assert result.added == ["aroha.testing"]


def test_school_admin_sees_only_own_students(login):
    c = login("admin.ktm")
    body = c.get("/schools/my/students/").content.decode()
    assert "bikash.thapa" in body and "tama.ngata" not in body

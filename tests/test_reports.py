"""test_reports.py - BI numbers, privacy, exports and access. Owner: Jihe Qi (QA)."""

import pytest

from apps.reports.services import BIService
from apps.schools.models import Section

pytestmark = pytest.mark.django_db


def test_platform_kpis_match_demo_data():
    k = BIService().platform_kpis()
    assert k["schools"] >= 4 and k["exams finished"] >= 19 and 0 <= k["pass rate %"] <= 100


def test_category_strength_sorted_weakest_first():
    rows = BIService().category_strength()
    assert rows and rows == sorted(rows, key=lambda r: r["percent"])


def test_class_report_has_no_parent_details():
    section = Section.objects.filter(students__isnull=False).first()
    rows = BIService().class_report(section)
    assert rows and not any("parent" in key for key in rows[0])


def test_exports(login):
    section = Section.objects.filter(school_class__school__code__isnull=False, students__isnull=False).first()
    client = login("superadmin")
    csv_resp = client.get(f"/reports/class/{section.pk}/?export=csv")
    assert csv_resp.status_code == 200 and csv_resp.content.startswith(b"First name")
    pdf = client.get(f"/reports/class/{section.pk}/?export=pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert client.get("/reports/bi/?export=csv").content.startswith(b"School")


def test_access_rules(login, user):
    assert login("superadmin").get("/reports/bi/").status_code == 200
    assert login("admin.brightstar").get("/reports/school/").status_code == 200
    assert login("sione.faleolo").get("/reports/class/").status_code == 200
    assert login("tama.ngata").get("/reports/bi/").status_code == 403
    other = Section.objects.exclude(school_class__school=user("sione.faleolo").school).first()
    assert login("sione.faleolo").get(f"/reports/class/{other.pk}/").status_code == 404

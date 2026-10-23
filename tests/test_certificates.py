"""test_certificates.py - Issue on pass, best score kept, PDF with QR, verify page, ZIP, share. Owner: Jihe Qi (QA)."""

import io
import zipfile

import pytest

from apps.certificates.models import Certificate
from apps.certificates.services import CertificateService
from apps.quizzes.models import QuizSession

pytestmark = pytest.mark.django_db


def test_demo_exams_issued_certificates():
    passed = QuizSession.objects.filter(mode="exam", status="finished", passed=True).count()
    assert (
        passed
        and Certificate.objects.count()
        == QuizSession.objects.filter(mode="exam", passed=True).values("student", "level").distinct().count()
    )


def test_issue_keeps_best_score():
    cert = Certificate.objects.first()
    session = cert.session
    session.percentage = min(100, cert.percentage + 5)
    session.save()
    CertificateService().issue_for(session)
    cert.refresh_from_db()
    assert cert.percentage == session.percentage


def test_failed_or_practice_gives_no_certificate():
    s = QuizSession.objects.filter(passed=False).first() or QuizSession.objects.filter(mode="practice").first()
    assert CertificateService().issue_for(s) is None


def test_pdf_and_verify():
    cert = Certificate.objects.select_related("student").first()
    pdf = CertificateService.pdf(cert, "http://testserver/certificates/verify/X/")
    assert pdf.startswith(b"%PDF")
    from django.test import Client  # pylint: disable=import-outside-toplevel

    page = Client().get(f"/certificates/verify/{cert.code}/")
    assert page.status_code == 200 and cert.student.last_name.encode() not in page.content


def test_download_access(login):
    cert = Certificate.objects.select_related("student").filter(student__school__code="BRIGHTSTAR").first()
    owner = login(cert.student.username, "Kiaora@2026")
    assert owner.get(f"/certificates/{cert.code}/download/").status_code == 200
    assert login("bikash.thapa").get(f"/certificates/{cert.code}/download/").status_code == 403
    assert login("sione.faleolo").get(f"/certificates/{cert.code}/download/").status_code == 200


def test_section_zip_and_share_links(login):
    cert = (
        Certificate.objects.select_related("student__student_profile__section")
        .filter(student__school__code="BRIGHTSTAR")
        .first()
    )
    data = login("sione.faleolo").get(f"/certificates/section/{cert.student.student_profile.section_id}/zip/").content
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        assert zf.namelist()
    page = login(cert.student.username, "Kiaora@2026").get("/certificates/")
    assert b"wa.me" in page.content and b"facebook.com/sharer" in page.content

"""test_payments.py - Quotes with GST, payslip checks, approve/reject, receipts, privacy. Owner: Jihe Qi (QA)."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.clock import today
from apps.core.exceptions import AccessDeniedError, UploadRejectedError, ValidationError
from apps.licensing.models import License
from apps.licensing.services import LevelPackService
from apps.payments.models import Payment
from apps.payments.services import PaymentService

pytestmark = pytest.mark.django_db
PDF = b"%PDF-1.4\n% test payslip\n%%EOF\n"


def _slip(name="slip.pdf", data=PDF):
    return SimpleUploadedFile(name, data, content_type="application/pdf")


def test_quote_adds_15_percent_gst(user):
    q = PaymentService.quote(user("admin.ktm").school, "pack", level=4)
    assert q.gst == (q.amount_ex_gst * Decimal("0.15")).quantize(Decimal("0.01")) and q.total == q.amount_ex_gst + q.gst


def test_community_discount_halves_plan_price(user):
    kauri = user("admin.kauricoast").school
    full = PaymentService.quote(user("admin.tuivalley").school, "plan", "BASIC", 12)
    half = PaymentService.quote(kauri, "plan", "BASIC", 12)
    assert half.amount_ex_gst * 2 == full.amount_ex_gst and "community" in half.item


def test_submit_and_approve_adds_level_pack(user):
    admin, boss = user("admin.ktm"), user("superadmin")
    Payment.objects.filter(school=admin.school, status="pending").delete()
    p = PaymentService().submit(
        admin, purpose="pack", level=5, bank_reference="KTM-L5", paid_on=today(), payslip=_slip()
    )
    assert p.number.startswith("PAY-") and p.status == "pending"
    PaymentService().approve(p, boss)
    assert LevelPackService().has_pack(admin.school, 5) and p.status == "approved"
    assert PaymentService.receipt_pdf(p).startswith(b"%PDF")


def test_approve_plan_extends_licence(user):
    admin, boss = user("admin.tuivalley"), user("superadmin")
    Payment.objects.filter(school=admin.school).delete()
    p = PaymentService().submit(
        admin,
        purpose="plan",
        plan="STANDARD",
        months=3,
        bank_reference="TUI-3",
        paid_on=today() - timedelta(days=1),
        payslip=_slip(),
    )
    PaymentService().approve(p, boss)
    lic = License.objects.get(school=admin.school)
    assert lic.plan == "STANDARD" and lic.expiry_date > today()


def test_rules(user):
    admin = user("admin.brightstar")
    with pytest.raises(ValidationError):
        PaymentService().submit(admin, purpose="pack", level=2, bank_reference="X", paid_on=today(), payslip=_slip())
    with pytest.raises(ValidationError):
        PaymentService().submit(
            admin,
            purpose="plan",
            plan="BASIC",
            months=1,
            bank_reference="X",
            paid_on=today() + timedelta(days=3),
            payslip=_slip(),
        )
    with pytest.raises(UploadRejectedError):
        PaymentService().submit(
            admin,
            purpose="plan",
            plan="BASIC",
            months=1,
            bank_reference="X",
            paid_on=today(),
            payslip=_slip("slip.pdf", b"MZ\x90\x00not a pdf"),
        )
    with pytest.raises(AccessDeniedError):
        PaymentService().submit(
            user("sione.faleolo"),
            purpose="plan",
            plan="BASIC",
            months=1,
            bank_reference="X",
            paid_on=today(),
            payslip=_slip(),
        )


def test_reject_needs_reason_and_no_receipt(user):
    p = Payment.objects.filter(status="pending").first()
    with pytest.raises(ValidationError):
        PaymentService().reject(p, user("superadmin"), "")
    PaymentService().reject(p, user("superadmin"), "Amount does not match.")
    with pytest.raises(ValidationError):
        PaymentService.receipt_pdf(p)
    with pytest.raises(ValidationError):
        PaymentService().approve(p, user("superadmin"))  # already reviewed


def test_payslips_are_private(login):
    other = Payment.objects.exclude(school__code="BRIGHTSTAR").first()
    assert login("admin.brightstar").get(f"/payments/{other.pk}/payslip/").status_code == 404
    assert login("superadmin").get(f"/payments/{other.pk}/payslip/").status_code == 200
    assert login("sione.faleolo").get("/payments/").status_code == 403


def test_payment_pages(login):
    admin = login("admin.brightstar")
    assert admin.get("/payments/pay/").status_code == 200
    assert login("superadmin").get("/payments/?status=pending").status_code == 200

"""demo.py - Demo payments so the review queue, receipts and BI are not empty. Owner: Jihe Qi (test data)."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.core.clock import today
from apps.schools.models import School

from .models import Payment
from .services import PaymentService

User = get_user_model()
DEMO_PAYSLIP = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj\n"
    b"% DEMO PAYSLIP - not a real bank document\ntrailer<</Root 1 0 R>>\n%%EOF\n"
)


def _payment(code, purpose, ref, days_ago, status, *, plan="", months=0, level=None, note=""):
    school = School.objects.get(code=code)
    admin = User.objects.filter(role="school_admin", school=school).first()
    q = PaymentService.quote(school, purpose, plan, months, level)
    p = Payment(
        school=school,
        submitted_by=admin,
        purpose=purpose,
        plan=plan,
        months=months,
        level=level,
        amount_ex_gst=q.amount_ex_gst,
        gst=q.gst,
        total=q.total,
        bank_reference=ref,
        paid_on=today() - timedelta(days=days_ago),
        status=status,
        review_note=note,
    )
    p.payslip.save(f"demo_payslip_{ref}.pdf", ContentFile(DEMO_PAYSLIP), save=False)
    if status != Payment.PENDING:
        p.reviewed_by, p.reviewed_at = User.objects.filter(role="super_admin").first(), timezone.now() - timedelta(
            days=days_ago - 1
        )
    p.save()
    return p


def load_demo_payments() -> int:
    """Two waiting for review, one approved (receipt), one rejected (reason shown)."""
    _payment("TUIVALLEY", Payment.PLAN, "TUI-RENEW", 2, Payment.PENDING, plan="BASIC", months=12)
    _payment("KTMVALLEY", Payment.PACK, "KTM-L3", 1, Payment.PENDING, level=3)
    _payment("BRIGHTSTAR", Payment.PACK, "BSS-L2", 40, Payment.APPROVED, level=4, note="Thank you.")
    _payment(
        "KAURICOAST",
        Payment.PLAN,
        "KCK-001",
        3,
        Payment.REJECTED,
        plan="STANDARD",
        months=3,
        note="The payslip amount does not match the total. Please upload the right payslip.",
    )
    return 4

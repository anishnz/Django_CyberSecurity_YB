"""
services.py - Price quotes, payslip submit, approve / reject, PDF receipt
=========================================================================

Owner: Rajneesh Kumar (task R-17)

Prices on the website are before GST. GST (15 %) is added on the quote and receipt.
The community discount (50 %) applies to plan prices only.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.clock import today
from apps.core.exceptions import AccessDeniedError, ValidationError
from apps.core.models import SystemSettings
from apps.core.services import AuditService
from apps.licensing.models import License
from apps.licensing.plans import LEVEL_PACK_PRICES, PLAN_CLASSES, plan_for
from apps.licensing.services import LevelPackService, LicenseService
from apps.medialib.validators import check_upload

from .models import GST_RATE, Payment

PAID_PLANS = ("BASIC", "STANDARD", "UNLIMITED")
MONTH_CHOICES = (1, 3, 6, 12)
CENT = Decimal("0.01")


@dataclass
class Quote:
    """Price for one item (value object)."""

    item: str
    amount_ex_gst: Decimal
    gst: Decimal
    total: Decimal


def _notify(event, data):
    from apps.notifications.services import notify  # pylint: disable=import-outside-toplevel
    notify(event, data)


class PaymentService:
    """Everything about payments in one place."""

    @staticmethod
    def quote(school, purpose: str, plan: str = "", months: int = 0, level: int | None = None) -> Quote:
        if purpose == Payment.PLAN:
            if plan not in PAID_PLANS or months not in MONTH_CHOICES:
                raise ValidationError("Please choose a paid plan and 1, 3, 6 or 12 months.")
            lic = License.objects.filter(school=school).first()
            discount = bool(lic and lic.community_discount)
            monthly = plan_for(plan, today(), today(), discount).monthly_price()
            amount = monthly * months
            item = f"{PLAN_CLASSES[plan].DISPLAY_NAME} plan, {months} month{'s' if months != 1 else ''}"
            if discount:
                item += " (community discount)"
        elif purpose == Payment.PACK:
            if level not in LEVEL_PACK_PRICES:
                raise ValidationError("Please choose a Level Pack (Level 2 to 6).")
            if LevelPackService().has_pack(school, level):
                raise ValidationError(f"Your school already has Level {level}.")
            amount, item = LEVEL_PACK_PRICES[level], f"Level {level} Pack"
        else:
            raise ValidationError("Please choose what you are paying for.")
        amount = Decimal(amount).quantize(CENT)
        gst = (amount * GST_RATE).quantize(CENT, ROUND_HALF_UP)
        return Quote(item, amount, gst, amount + gst)

    @transaction.atomic
    def submit(self, user, *, purpose, plan="", months=0, level=None, bank_reference, paid_on, payslip, request=None):
        if not user.is_school_admin:
            raise AccessDeniedError("Only the School Admin can send payments.")
        if paid_on > today() or paid_on < today() - timedelta(days=60):
            raise ValidationError("The payment date must be in the last 60 days.")
        if Payment.objects.filter(school=user.school, status=Payment.PENDING, purpose=purpose,
                                  level=level if purpose == Payment.PACK else None).exists():
            raise ValidationError("You already have a payment like this waiting for review.")
        check_upload(payslip, "payslip", request, user)
        q = self.quote(user.school, purpose, plan, months, level)
        payment = Payment.objects.create(
            school=user.school, submitted_by=user, purpose=purpose, plan=plan if purpose == Payment.PLAN else "",
            months=months if purpose == Payment.PLAN else 0, level=level if purpose == Payment.PACK else None,
            amount_ex_gst=q.amount_ex_gst, gst=q.gst, total=q.total, bank_reference=bank_reference.strip()[:40],
            paid_on=paid_on, payslip=payslip)
        AuditService.log(user, "payment_submitted", payment.number, new=f"{q.item} ${q.total}")
        _notify("payment_submitted", {"school": user.school.name, "item": q.item, "amount": q.total})
        return payment

    @staticmethod
    def _new_expiry(school, months: int) -> date:
        """Add months after the current expiry (or after today if it already ended)."""
        lic = License.objects.filter(school=school).first()
        start = max(today(), lic.expiry_date) if lic and lic.plan != "TRIAL" and lic.expiry_date.year < 9000 else today()
        return start + timedelta(days=30 * months)

    @transaction.atomic
    def approve(self, payment: Payment, user, note: str = "") -> Payment:
        self._check_reviewer(payment, user)
        if payment.purpose == Payment.PLAN:
            expiry = None if payment.plan == "UNLIMITED" else self._new_expiry(payment.school, payment.months)
            LicenseService().set_plan(payment.school, payment.plan, expiry, user, key=payment.number)
        else:
            LevelPackService.add_pack(payment.school, payment.level, user, key=payment.number)
        return self._finish(payment, user, Payment.APPROVED, note)

    @transaction.atomic
    def reject(self, payment: Payment, user, note: str) -> Payment:
        self._check_reviewer(payment, user)
        if len(note.strip()) < 5:
            raise ValidationError("Please tell the school why (at least 5 characters).")
        return self._finish(payment, user, Payment.REJECTED, note)

    @staticmethod
    def _check_reviewer(payment, user):
        if not user.is_super_admin:
            raise AccessDeniedError("Only the Super Admin can review payments.")
        if payment.status != Payment.PENDING:
            raise ValidationError("This payment was already reviewed.")

    @staticmethod
    def _finish(payment, user, status, note):
        payment.status, payment.review_note = status, note.strip()[:300]
        payment.reviewed_by, payment.reviewed_at = user, timezone.now()
        payment.save()
        AuditService.log(user, f"payment_{status}", payment.number, "pending", status, details=note)
        _notify("payment_reviewed", {"school_id": payment.school_id, "status": status, "item": payment.item})
        admin = payment.submitted_by
        if admin and admin.email:
            from apps.emails.services import EmailService  # pylint: disable=import-outside-toplevel
            EmailService().send_template("payment_reviewed", admin.email, {
                "name": admin.first_name or admin.username, "status": status, "reference": payment.number,
                "note": note or ""})
        return payment

    # ------------------------------------------------------------ receipt
    @staticmethod
    def receipt_pdf(payment: Payment) -> bytes:
        """Tax receipt (approved payments only)."""
        # pylint: disable=import-outside-toplevel
        from django.conf import settings
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from apps.core.pdf import register_fonts, styles as pdf_styles
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        if payment.status != Payment.APPROVED:
            raise ValidationError("A receipt is only made after the payment is approved.")
        cfg, proj = SystemSettings.load(), settings.PROJECT
        styles = pdf_styles()
        regular, bold = register_fonts()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, title=f"Receipt {payment.number}")
        rows = [["Item", "Amount (NZD)"], [payment.item, f"{payment.amount_ex_gst:,.2f}"],
                ["GST 15%", f"{payment.gst:,.2f}"], ["Total paid", f"{payment.total:,.2f}"]]
        table = Table(rows, colWidths=[330, 140])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E3B43")),
                                   ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                                   ("FONTNAME", (0, 0), (-1, -1), regular), ("FONTNAME", (0, -1), (-1, -1), bold), ("FONTNAME", (0, 0), (-1, 0), bold),
                                   ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D3DFE1"))]))
        story = [Paragraph(f"{proj['company']} – Tax receipt", styles["Title"]),
                 Paragraph(f"{proj['company_address']} · GST number {cfg.gst_number}", styles["Normal"]), Spacer(1, 12),
                 Paragraph(f"<b>Receipt:</b> {payment.number} &nbsp; <b>Date approved:</b> "
                           f"{payment.reviewed_at:%d %b %Y}", styles["Normal"]),
                 Paragraph(f"<b>Customer:</b> {payment.school.name} ({payment.school.code})", styles["Normal"]),
                 Paragraph(f"<b>Bank reference:</b> {payment.bank_reference} &nbsp; <b>Paid on:</b> "
                           f"{payment.paid_on:%d %b %Y}", styles["Normal"]), Spacer(1, 12), table, Spacer(1, 18),
                 Paragraph("Thank you – ngā mihi. This is a student project demo receipt "
                           f"({proj['code']}).", styles["Italic"])]
        doc.build(story)
        return buf.getvalue()

"""
models.py - Payments by bank transfer with payslip upload and manual approval
==============================================================================

Owner: Rajneesh Kumar (task R-17). Screens by Dinesh Upreti.

Flow: School Admin picks a plan or Level Pack → sees the price with GST and the
bank details → pays at the bank → uploads the payslip → Super Admin approves
(licence or pack is added automatically, PDF receipt) or rejects with a reason.
No card details are ever stored (no online card payment).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import models

GST_RATE = Decimal("0.15")


def payslip_path(instance, filename: str) -> str:
    return f"payslips/{instance.school_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()[:6]}"


class Payment(models.Model):
    """One payment for a licence plan (months) or a Level Pack."""

    PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
    STATUSES = [(PENDING, "Waiting for review"), (APPROVED, "Approved"), (REJECTED, "Rejected")]
    PLAN, PACK = "plan", "pack"
    PURPOSES = [(PLAN, "Licence plan"), (PACK, "Level Pack")]

    number = models.CharField(max_length=12, unique=True, editable=False)
    school = models.ForeignKey("schools.School", on_delete=models.CASCADE, related_name="payments")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    purpose = models.CharField(max_length=5, choices=PURPOSES)
    plan = models.CharField(max_length=20, blank=True)
    months = models.PositiveSmallIntegerField(default=0)
    level = models.PositiveSmallIntegerField(null=True, blank=True)
    amount_ex_gst = models.DecimalField(max_digits=10, decimal_places=2)
    gst = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    bank_reference = models.CharField(max_length=40, help_text="The reference you typed at the bank.")
    paid_on = models.DateField()
    payslip = models.FileField(upload_to=payslip_path)
    status = models.CharField(max_length=10, choices=STATUSES, default=PENDING, db_index=True)
    review_note = models.CharField(max_length=300, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.number} {self.item}"

    def save(self, *args, **kwargs):
        if not self.number:
            last = Payment.objects.order_by("-pk").values_list("pk", flat=True).first() or 0
            self.number = f"PAY-{last + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def item(self) -> str:
        if self.purpose == self.PACK:
            return f"Level {self.level} Pack"
        return f"{self.plan.title()} plan, {self.months} month{'s' if self.months != 1 else ''}"

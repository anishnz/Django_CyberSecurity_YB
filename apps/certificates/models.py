"""
models.py - Level certificates (Tohu)
=====================================

Owner: Dinesh Upreti (task D-16). One certificate per student per level; a
better score later updates it. Each one has a short public code so anyone can
check it is real at /certificates/verify/<code>/ (the QR code on the PDF).
"""

from __future__ import annotations

import secrets

from django.conf import settings
from django.db import models


def _code() -> str:
    return secrets.token_hex(5).upper()


class Certificate(models.Model):
    """One certificate per student per level (keeps the best score)."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    level = models.ForeignKey("learning.Level", on_delete=models.CASCADE)
    session = models.ForeignKey("quizzes.QuizSession", null=True, on_delete=models.SET_NULL, related_name="+")
    code = models.CharField(max_length=12, unique=True, default=_code)
    student_name = models.CharField(max_length=120, help_text="Name printed on the certificate.")
    school_name = models.CharField(max_length=120, blank=True)
    percentage = models.FloatField()
    awareness_level = models.CharField(max_length=30, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ["level__number"]
        constraints = [models.UniqueConstraint(fields=["student", "level"], name="one_certificate_per_level")]

    def __str__(self) -> str:
        return f"{self.student_name} – Level {self.level.number}"

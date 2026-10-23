"""models.py - Notifications shown under the bell icon. Owner: Rajneesh Kumar (task R-08)."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class Notification(models.Model):
    """One message for one user."""

    KINDS = [("info", "Info"), ("success", "Success"), ("warning", "Warning"), ("danger", "Danger")]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=300)
    kind = models.CharField(max_length=10, choices=KINDS, default="info")
    icon = models.CharField(max_length=40, default="bell")
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.message

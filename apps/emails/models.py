"""
models.py - Email templates, sent-email log and unsubscribe list
================================================================

Owner: Rajneesh Kumar (task R-14). Screens by Dinesh Upreti.

Templates use {placeholders} such as {name}, {ticket}, {school}. The Super Admin
can edit the text; the key stays the same so the code always finds it.
"""
from __future__ import annotations

import secrets

from django.db import models


class EmailTemplate(models.Model):
    """An editable email (subject + body) used by the system or for bulk mail."""

    AUDIENCES = [("system", "System (automatic)"), ("parents", "Parents / whānau"), ("teachers", "Teachers"),
                 ("admins", "School Admins")]

    key = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    audience = models.CharField(max_length=10, choices=AUDIENCES, default="system")
    subject = models.CharField(max_length=150)
    body = models.TextField(max_length=5000, help_text="Use {name}, {school}, {ticket}, {title}, {reply}, {link}.")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["audience", "name"]

    def __str__(self) -> str:
        return self.name


class EmailLog(models.Model):
    """Every email the system tried to send (sent, failed or skipped)."""

    SENT, FAILED, SKIPPED = "sent", "failed", "skipped"
    STATUSES = [(SENT, "Sent"), (FAILED, "Failed"), (SKIPPED, "Skipped")]

    to = models.EmailField()
    subject = models.CharField(max_length=200)
    template_key = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES)
    via = models.CharField(max_length=20, blank=True, help_text="gmail or local")
    error = models.CharField(max_length=300, blank=True)
    batch = models.CharField(max_length=20, blank=True, help_text="Bulk send id")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]


def _token() -> str:
    return secrets.token_urlsafe(16)


class Unsubscribe(models.Model):
    """People who asked for no more bulk emails (system emails still go)."""

    email = models.EmailField(unique=True)
    token = models.CharField(max_length=40, unique=True, default=_token)
    unsubscribed = models.BooleanField(default=False)
    changed_at = models.DateTimeField(auto_now=True)

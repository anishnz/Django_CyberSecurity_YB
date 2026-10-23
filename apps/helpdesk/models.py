"""
models.py - Help desk tickets (Tautoko)
=======================================

Owner: Rajneesh Kumar (task R-13). Screens by Dinesh Upreti.

Ticket numbers look like CQ-0042. Status flow (state machine in services.py):
Open → Assigned → In progress → Waiting for user → Resolved → Closed (reopen within 7 days).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


class Ticket(models.Model):
    """A question or problem raised by any user (or by the Contact us form / email)."""

    OPEN, ASSIGNED, IN_PROGRESS, WAITING, RESOLVED, CLOSED = (
        "open",
        "assigned",
        "in_progress",
        "waiting",
        "resolved",
        "closed",
    )
    STATUSES = [
        (OPEN, "Open"),
        (ASSIGNED, "Assigned"),
        (IN_PROGRESS, "In progress"),
        (WAITING, "Waiting for user"),
        (RESOLVED, "Resolved"),
        (CLOSED, "Closed"),
    ]
    CATEGORIES = [
        ("login", "Login and password"),
        ("licence", "Licence and payment"),
        ("quiz", "Quiz or exam problem"),
        ("content", "Content error"),
        ("bug", "Something is broken"),
        ("feature", "Feature idea"),
        ("contact", "Website contact"),
        ("other", "Other"),
    ]
    PRIORITIES = [("urgent", "Urgent"), ("high", "High"), ("normal", "Normal"), ("low", "Low")]

    number = models.CharField(max_length=12, unique=True, editable=False)
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=5000)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="other")
    priority = models.CharField(max_length=10, choices=PRIORITIES, default="normal")
    status = models.CharField(max_length=15, choices=STATUSES, default=OPEN, db_index=True)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets"
    )
    requester_email = models.EmailField(blank=True, help_text="For tickets from the website or email.")
    requester_name = models.CharField(max_length=120, blank=True)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tickets"
    )
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.SET_NULL)
    question = models.ForeignKey(
        "learning.Question",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Set by 'Report this question'.",
    )
    sla_due = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.number} {self.title}"

    def save(self, *args, **kwargs):
        """Give new tickets the next number CQ-0001, CQ-0002 …"""
        if not self.number:
            last = Ticket.objects.order_by("-pk").values_list("pk", flat=True).first() or 0
            self.number = f"CQ-{last + 1:04d}"
        super().save(*args, **kwargs)

    @property
    def is_open(self) -> bool:
        return self.status not in (self.RESOLVED, self.CLOSED)

    @property
    def who(self) -> str:
        return str(self.requester) if self.requester else f"{self.requester_name} <{self.requester_email}>"


def attachment_path(instance, filename: str) -> str:
    return f"tickets/{instance.comment.ticket.number}/{uuid.uuid4().hex}{Path(filename).suffix.lower()[:6]}"


class TicketComment(models.Model):
    """A reply on a ticket. Internal notes are only seen by staff."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    author_name = models.CharField(max_length=120, blank=True)
    body = models.TextField(max_length=5000)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class TicketAttachment(models.Model):
    """A screenshot or file attached to a comment (images and PDF only, size limited)."""

    comment = models.ForeignKey(TicketComment, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=attachment_path)
    original_name = models.CharField(max_length=200)
    size_bytes = models.PositiveIntegerField(default=0)


class TicketHistory(models.Model):
    """Every change to a ticket (status, assignee, priority)."""

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="history")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    field = models.CharField(max_length=30)
    old_value = models.CharField(max_length=100, blank=True)
    new_value = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

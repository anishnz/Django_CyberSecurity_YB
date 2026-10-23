"""
models.py - AI drafts and the two human approvals
=================================================

Owner: Anish Shrestha (task A-20) with Jihe Qi (AI adapters)

An AI draft is NEVER shown to students straight away. A teacher checks the facts,
and when the text has Māori language or tikanga the Cultural Guide (Kaiārahi)
checks it too. Only then is it "approved" and can it be published.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class AIDraft(models.Model):
    """A draft made by AI that people must approve before use."""

    QUESTION, TIP, PARENT, EXPLAIN = "question", "tip", "parent_message", "explanation"
    KINDS = [
        (QUESTION, "Practice question"),
        (TIP, "Safety tip"),
        (PARENT, "Message to parents / whānau"),
        (EXPLAIN, "Simple explanation of a topic"),
    ]
    DRAFT, APPROVED, REJECTED, PUBLISHED = "draft", "approved", "rejected", "published"
    STATUSES = [
        (DRAFT, "Waiting for approval"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
        (PUBLISHED, "Published"),
    ]

    kind = models.CharField(max_length=20, choices=KINDS, default=QUESTION)
    topic = models.ForeignKey("learning.LearningTopic", null=True, blank=True, on_delete=models.SET_NULL)
    request_text = models.CharField(max_length=300, help_text="What you asked for.")
    text = models.TextField(max_length=4000)
    provider = models.CharField(max_length=40, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=DRAFT, db_index=True)
    needs_cultural_check = models.BooleanField(default=False)
    teacher_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    cultural_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    review_note = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="ai_drafts"
    )
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.CASCADE)
    question = models.ForeignKey(
        "learning.Question",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The practice question made from this draft.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.request_text[:40]}"

    @property
    def teacher_ok(self) -> bool:
        return self.teacher_approved_by_id is not None

    @property
    def cultural_ok(self) -> bool:
        return not self.needs_cultural_check or self.cultural_approved_by_id is not None

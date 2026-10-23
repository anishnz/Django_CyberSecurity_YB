"""
models.py - Announcements (Pānui) shown on dashboards
=====================================================

Owner: Rajneesh Kumar (task R-18). Screens by Dinesh Upreti.
Super Admin → all schools or one school; School Admin → own school only.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models

AUDIENCES = [("all", "Everyone"), ("staff", "Staff only (admins and teachers)"), ("students", "Students only")]


class Announcement(models.Model):
    title = models.CharField(max_length=120)
    body = models.TextField(max_length=2000)
    audience = models.CharField(max_length=10, choices=AUDIENCES, default="all")
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.CASCADE,
                               help_text="Empty = every school (Super Admin only).")
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True, help_text="Empty = until you remove it.")
    is_pinned = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_pinned", "-starts_on", "-created_at"]

    def __str__(self) -> str:
        return self.title

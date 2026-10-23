"""
models.py - Public website content: slider and contact messages
===============================================================

Owner: Dinesh Upreti (public website)
"""

from __future__ import annotations

from django.db import models


class Slide(models.Model):
    """One picture in the home page slider. Super Admin can upload AI-made images later."""

    title = models.CharField(max_length=100)
    caption = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to="website/slides/",
        blank=True,
        help_text="Optional upload (max 5 MB). Without it, the built-in illustration is used.",
    )
    static_image = models.CharField(max_length=120, blank=True, help_text="Built-in illustration in static/img/slides/")
    order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class ContactMessage(models.Model):
    """A message from the Contact us form. It also becomes a help desk ticket."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    organisation = models.CharField(max_length=120, blank=True)
    topic = models.CharField(max_length=40, default="general")
    message = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    ticket_number = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name}: {self.topic}"

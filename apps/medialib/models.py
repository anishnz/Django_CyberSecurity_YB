"""
models.py - Uploaded images, audio, video and YouTube embeds
============================================================

Owner: Jihe Qi (task J-12)

Only staff can upload. Every file is checked for its real type (file
signature) and size limit before it is saved (see validators.py).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


def upload_path(instance, filename: str) -> str:
    """Safe random file name: media/<kind>/<uuid>.<ext> (the user's file name is never used on disk)."""
    ext = Path(filename).suffix.lower()[:6]
    return f"library/{instance.kind}/{uuid.uuid4().hex}{ext}"


class MediaFile(models.Model):
    """An image, audio clip, video or document used in lessons."""

    IMAGE, AUDIO, VIDEO, DOCUMENT = "image", "audio", "video", "document"
    KINDS = [(IMAGE, "Image"), (AUDIO, "Audio"), (VIDEO, "Video"), (DOCUMENT, "Document (PDF)")]

    kind = models.CharField(max_length=10, choices=KINDS)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    alt_text = models.CharField(max_length=200, blank=True, help_text="Describe the image for screen readers.")
    file = models.FileField(upload_to=upload_path)
    mime_type = models.CharField(max_length=60, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    topic = models.ForeignKey(
        "learning.LearningTopic", null=True, blank=True, on_delete=models.SET_NULL, related_name="media"
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=True)
    needs_cultural_check = models.BooleanField(
        default=False,
        verbose_name="Has Māori language, images or tikanga",
        help_text="Students only see it after the Cultural Guide (Kaiārahi) checks it.",
    )
    cultural_check = models.BooleanField(default=False, help_text="Checked by the Kaiārahi (culturally safe).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.title}"

    @property
    def visible_to_students(self) -> bool:
        return self.is_published and (self.cultural_check or not self.needs_cultural_check)


class VideoEmbed(models.Model):
    """A YouTube video shown on a topic page (privacy-enhanced nocookie link)."""

    topic = models.ForeignKey(
        "learning.LearningTopic", null=True, blank=True, on_delete=models.CASCADE, related_name="videos"
    )
    title = models.CharField(max_length=120)
    url = models.URLField()
    video_id = models.CharField(max_length=11)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    school = models.ForeignKey(
        "schools.School",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Empty = every school (Super Admin).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def embed_url(self) -> str:
        return f"https://www.youtube-nocookie.com/embed/{self.video_id}"

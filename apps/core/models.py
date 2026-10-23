"""
models.py - Core models: system settings (Singleton), audit log, feature switches, backups
==========================================================================================

Owners: Anish Shrestha (SystemSettings, task A-16); Rajneesh Kumar (AuditLog, FeatureSwitch,
BackupRecord, tasks R-14 to R-16)

Concepts:
    * Singleton pattern: SystemSettings always has exactly ONE row (pk=1).
      ``SystemSettings.load()`` is the single global access point.
    * Encapsulation: other code never edits settings directly; it calls
      ``SettingsService`` (core/services.py) which validates and audits.
"""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SystemSettings(models.Model):
    """Every system-wide rule the Super Admin can change (one row only)."""

    default_section_capacity = models.PositiveSmallIntegerField(
        default=35, validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Default number of students allowed in a new section.")
    exam_pass_mark = models.PositiveSmallIntegerField(
        default=70, validators=[MinValueValidator(50), MaxValueValidator(100)],
        help_text="Percentage needed to pass a level exam.")
    practice_question_count = models.PositiveSmallIntegerField(
        default=10, validators=[MinValueValidator(5), MaxValueValidator(20)],
        help_text="Number of questions in a practice quiz.")
    temp_account_minutes = models.PositiveSmallIntegerField(
        default=15, validators=[MinValueValidator(5), MaxValueValidator(240)],
        help_text="How long a temporary account works.")
    license_warning_days = models.PositiveSmallIntegerField(
        default=14, validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Warn School Admins this many days before a licence ends.")
    image_max_mb = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(20)])
    audio_max_mb = models.PositiveSmallIntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(50)])
    video_max_mb = models.PositiveSmallIntegerField(default=100, validators=[MinValueValidator(5), MaxValueValidator(500)])
    document_max_mb = models.PositiveSmallIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(25)])
    force_mfa_for_admins = models.BooleanField(default=False, help_text="Admins must use two-step login.")
    maintenance_mode = models.BooleanField(default=False, help_text="Show 'Back soon' to everyone except Super Admins.")
    maintenance_message = models.CharField(max_length=200, default="CyberQuest is being updated. Please come back soon.")
    contact_email = models.EmailField(default="hello@cyberquest.local")
    contact_phone = models.CharField(max_length=40, default="+64 9 000 0000")
    welcome_video_url = models.URLField(blank=True, help_text="YouTube link shown on the public home page.")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=150, blank=True)

    # Fields shown on the settings page, with their friendly names.
    EDITABLE = [
        "default_section_capacity", "exam_pass_mark", "practice_question_count", "temp_account_minutes",
        "license_warning_days", "image_max_mb", "audio_max_mb", "video_max_mb", "document_max_mb",
        "force_mfa_for_admins", "maintenance_mode", "maintenance_message", "contact_email",
        "contact_phone", "welcome_video_url",
    ]

    class Meta:
        verbose_name = "System settings"
        verbose_name_plural = "System settings"

    def __str__(self) -> str:
        return "CyberQuest system settings"

    def save(self, *args, **kwargs):
        """Singleton rule: always save as row 1."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """The settings row can never be deleted."""
        return (0, {})

    @classmethod
    def load(cls) -> "SystemSettings":
        """Return the one settings row, creating it with defaults the first time."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def max_bytes(self, kind: str) -> int:
        """Upload size limit in bytes for 'image', 'audio', 'video' or 'document'."""
        mb = {"image": self.image_max_mb, "audio": self.audio_max_mb, "video": self.video_max_mb,
              "document": self.document_max_mb}.get(kind, self.document_max_mb)
        return mb * 1024 * 1024


class AuditLog(models.Model):
    """Who changed what, and when (old value → new value)."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=60, db_index=True)
    target = models.CharField(max_length=200, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.username} {self.action}"


class FeatureSwitch(models.Model):
    """Turn a feature on or off without changing code (e.g. 'ai', 'whatsapp')."""

    key = models.SlugField(max_length=40, unique=True)
    label = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return f"{self.label} ({'on' if self.enabled else 'off'})"

    @classmethod
    def is_on(cls, key: str, default: bool = True) -> bool:
        """True when the feature is switched on (unknown keys use the default)."""
        row = cls.objects.filter(key=key).only("enabled").first()
        return default if row is None else row.enabled


class BackupRecord(models.Model):
    """A database backup file made by the Super Admin or the backup command."""

    file_name = models.CharField(max_length=200, unique=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    reason = models.CharField(max_length=60, default="manual")
    created_by = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.file_name

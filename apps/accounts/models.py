"""
models.py - User accounts, MFA backup codes and "Login as" sessions
===================================================================

Owner: Anish Shrestha (tasks A-05, A-08, A-09)

Concepts:
    * Inheritance: ``User`` extends Django's AbstractUser (password hashing,
      sessions and permissions come for free).
    * Encapsulation: the MFA secret is stored encrypted and only read through
      ``get_mfa_secret()`` / ``set_mfa_secret()``.
    * Composition: ``user.role_obj`` returns a Role object (roles.py) that knows
      the dashboard and menu for that role.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone

from apps.core import crypto

from .roles import ROLE_CHOICES, role_for


class CyberQuestUserManager(UserManager):
    """Extra queries used across the app (Repository idea)."""

    def active(self):
        """Users who are switched on."""
        return self.filter(is_active=True)

    def in_school(self, school):
        """Users that belong to one school."""
        return self.filter(school=school)

    def with_role(self, role: str):
        """Users with one role code."""
        return self.filter(role=role)


class User(AbstractUser):
    """A CyberQuest user. ``role`` decides what they can do."""

    SUPER_ADMIN, SCHOOL_ADMIN, TEACHER, STUDENT, GUEST = "super_admin", "school_admin", "teacher", "student", "guest"

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STUDENT, db_index=True)
    school = models.ForeignKey("schools.School", null=True, blank=True, on_delete=models.SET_NULL,
                               related_name="users")
    phone = models.CharField(max_length=30, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Temporary accounts stop working after this time.")
    is_temporary = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    _mfa_secret = models.TextField(blank=True, db_column="mfa_secret")
    locked_until = models.DateTimeField(null=True, blank=True)
    failed_logins = models.PositiveSmallIntegerField(default=0)
    tour_finished = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False, help_text="Created by the demo data loader.")
    is_cultural_guide = models.BooleanField(
        default=False, verbose_name="Cultural Guide (Kaiārahi)",
        help_text="Can give the cultural approval for AI drafts and media with Māori content.")
    demo_password = models.CharField(max_length=40, blank=True,
                                     help_text="Known password of a DEMO account only (shown on the demo page).")

    objects = CyberQuestUserManager()

    class Meta:
        ordering = ["first_name", "last_name"]
        indexes = [models.Index(fields=["role", "school"])]

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    # ------------------------------------------------------------ role helpers
    @property
    def role_obj(self):
        """The Role object for this user (polymorphism)."""
        return role_for(self.role)

    @property
    def is_super_admin(self) -> bool:
        return self.role == self.SUPER_ADMIN

    @property
    def is_school_admin(self) -> bool:
        return self.role == self.SCHOOL_ADMIN

    @property
    def is_teacher(self) -> bool:
        return self.role == self.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == self.STUDENT

    @property
    def is_guest(self) -> bool:
        return self.role == self.GUEST

    @property
    def display_name(self) -> str:
        return self.first_name or self.username

    # ------------------------------------------------------------ account state
    def is_expired(self, now=None) -> bool:
        """True when a temporary account has passed its end time."""
        now = now or timezone.now()
        return bool(self.expires_at and now >= self.expires_at)

    def is_locked(self, now=None) -> bool:
        """True while the account is locked after too many wrong passwords."""
        now = now or timezone.now()
        return bool(self.locked_until and now < self.locked_until)

    # ------------------------------------------------------------- MFA secret
    def get_mfa_secret(self) -> str:
        """Decrypt and return the TOTP secret."""
        return crypto.decrypt(self._mfa_secret)

    def set_mfa_secret(self, secret: str) -> None:
        """Encrypt and store the TOTP secret."""
        self._mfa_secret = crypto.encrypt(secret)


class MFABackupCode(models.Model):
    """One-time backup codes for two-step login (stored as hashes)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="backup_codes")
    code_hash = models.CharField(max_length=128)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Backup code for {self.user}"


class ImpersonationSession(models.Model):
    """Record of a Super Admin using "Login as" (for testing and support)."""

    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="impersonations")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="impersonated_by")
    reason = models.CharField(max_length=200)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.admin} as {self.target}"

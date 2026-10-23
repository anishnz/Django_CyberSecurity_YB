"""
models.py - Security log
========================

Owner: Anish Shrestha (task A-17)

Every security-related event is saved with time, user, IP address and browser:
logins, failed logins, lockouts, access denied, "Login as", MFA changes,
rejected uploads and API key changes.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class SecurityEvent(models.Model):
    """One security event."""

    LOGIN, LOGIN_FAILED, LOCKED, LOGOUT = "login", "login_failed", "account_locked", "logout"
    BLOCKED, ACCESS_DENIED = "login_blocked", "access_denied"
    IMPERSONATE_START, IMPERSONATE_STOP = "login_as_start", "login_as_stop"
    MFA_ON, MFA_OFF, MFA_FAILED = "mfa_enabled", "mfa_disabled", "mfa_failed"
    UPLOAD_REJECTED, KEY_CHANGED, PASSWORD_RESET = "upload_rejected", "api_key_changed", "password_reset"

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, blank=True)
    event = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    path = models.CharField(max_length=300, blank=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.event} {self.username}"

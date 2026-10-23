"""
services.py - Security log and login lockout
============================================

Owner: Anish Shrestha (task A-17)

Rules:
    * After 5 wrong passwords (setting), the account is locked for 15 minutes.
    * A correct login resets the counter.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import SecurityEvent

logger = logging.getLogger("cyberquest")


def client_ip(request) -> str | None:
    """The visitor's IP address (first entry of X-Forwarded-For if present)."""
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) or None


class SecurityLog:
    """Write security events."""

    @staticmethod
    def record(event: str, request=None, user=None, username: str = "", details: str = "") -> SecurityEvent:
        """Save one security event and copy it to the log file."""
        name = username or getattr(user, "username", "") or ""
        entry = SecurityEvent.objects.create(
            event=event, user=user if getattr(user, "pk", None) else None, username=name,
            ip_address=client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:300] if request else ""),
            path=(request.path[:300] if request else ""), details=details)
        logger.info("SECURITY %s user=%s ip=%s %s", event, name, entry.ip_address, details)
        return entry


class LockoutService:
    """Lock an account after too many wrong passwords."""

    def __init__(self):
        self.max_attempts = settings.CYBERQUEST["LOCKOUT_ATTEMPTS"]
        self.minutes = settings.CYBERQUEST["LOCKOUT_MINUTES"]

    def register_failure(self, user, request=None) -> bool:
        """Count a wrong password. Returns True if the account is now locked."""
        user.failed_logins += 1
        locked = user.failed_logins >= self.max_attempts
        if locked:
            user.locked_until = timezone.now() + timedelta(minutes=self.minutes)
            user.failed_logins = 0
            SecurityLog.record(SecurityEvent.LOCKED, request, user, details=f"locked for {self.minutes} minutes")
        user.save(update_fields=["failed_logins", "locked_until"])
        return locked

    @staticmethod
    def register_success(user) -> None:
        """Reset the counter after a correct login."""
        if user.failed_logins or user.locked_until:
            user.failed_logins = 0
            user.locked_until = None
            user.save(update_fields=["failed_logins", "locked_until"])

    @staticmethod
    def unlock(user, by=None, request=None) -> None:
        """Super Admin unlocks an account straight away."""
        user.failed_logins = 0
        user.locked_until = None
        user.save(update_fields=["failed_logins", "locked_until"])
        SecurityLog.record("account_unlocked", request, user, details=f"by {getattr(by, 'username', '')}")

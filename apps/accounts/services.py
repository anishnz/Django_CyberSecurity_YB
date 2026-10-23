"""
services.py - Login checks, two-step login (MFA), "Login as" and user management
================================================================================

Owner: Anish Shrestha (tasks A-06 to A-10)

Concepts:
    * Service classes keep the rules in one place: views only call them.
    * MFA uses TOTP (time-based one-time password, the same as Google
      Authenticator / Microsoft Authenticator) via the ``pyotp`` library.
    * "Login as" keeps the Super Admin's id in the session so they can return.
"""

from __future__ import annotations

import hashlib
import io
import re
import secrets
from datetime import timedelta

import pyotp
import qrcode
import qrcode.image.svg
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import AccessDeniedError, LicenseExpiredError, ValidationError
from apps.core.models import SystemSettings
from apps.core.services import AuditService
from apps.security.models import SecurityEvent
from apps.security.services import SecurityLog

from .models import ImpersonationSession, MFABackupCode

User = get_user_model()
IMPERSONATOR_KEY = "impersonator_id"
IMPERSONATION_KEY = "impersonation_session_id"
MFA_PENDING_KEY = "mfa_pending_user_id"


class AccountCheck:
    """Decide whether a user may use CyberQuest right now (FR-02)."""

    @staticmethod
    def problem(user) -> str | None:
        """Return a friendly reason the user cannot log in, or None if all is fine."""
        if not user.is_active:
            return "This account is switched off. Please contact your School Admin."
        if user.is_expired():
            return "This temporary account has expired."
        if user.is_student:
            profile = getattr(user, "student_profile", None)
            if profile is None or not profile.family_consent:
                return "Your family (whānau) consent form is still waiting. Please ask your teacher."
        if user.school_id and not user.is_super_admin:
            if not user.school.is_active:
                return "Your school's account is switched off. Please contact CyberQuest support."
            from apps.licensing.services import LicenseService  # pylint: disable=import-outside-toplevel

            if not LicenseService().is_school_active(user.school):
                return LicenseExpiredError.default_message
        return None


class MFAService:
    """Two-step login with an authenticator app (FR-05)."""

    ISSUER = "CyberQuest"

    @staticmethod
    def new_secret() -> str:
        return pyotp.random_base32()

    def provisioning_uri(self, user, secret: str) -> str:
        """The otpauth:// link that the QR code holds."""
        return pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name=self.ISSUER)

    def qr_svg(self, user, secret: str) -> str:
        """QR code as inline SVG text (no image file needed)."""
        img = qrcode.make(self.provisioning_uri(user, secret), image_factory=qrcode.image.svg.SvgPathImage, box_size=8)
        buf = io.BytesIO()
        img.save(buf)
        return buf.getvalue().decode()

    @staticmethod
    def verify(secret: str, code: str) -> bool:
        """True if the 6-digit code is right (allows 30 seconds clock difference)."""
        code = re.sub(r"\s", "", code or "")
        return bool(secret) and code.isdigit() and pyotp.TOTP(secret).verify(code, valid_window=1)

    @staticmethod
    def _hash(code: str) -> str:
        return hashlib.sha256(code.strip().upper().encode()).hexdigest()

    def make_backup_codes(self, user, count: int = 8) -> list[str]:
        """Create new one-time backup codes (old ones are removed). Shown only once."""
        user.backup_codes.all().delete()
        codes = [secrets.token_hex(4).upper() for _ in range(count)]
        MFABackupCode.objects.bulk_create([MFABackupCode(user=user, code_hash=self._hash(c)) for c in codes])
        return codes

    def use_backup_code(self, user, code: str) -> bool:
        """Accept a backup code once."""
        row = user.backup_codes.filter(code_hash=self._hash(code), used_at__isnull=True).first()
        if row is None:
            return False
        row.used_at = timezone.now()
        row.save(update_fields=["used_at"])
        return True

    def enable(self, user, secret: str, code: str, request=None) -> list[str]:
        """Turn MFA on after the user proves the app works."""
        if not self.verify(secret, code):
            raise ValidationError("That code is not right. Check the time on your phone and try again.")
        user.set_mfa_secret(secret)
        user.mfa_enabled = True
        user.save(update_fields=["_mfa_secret", "mfa_enabled"])
        SecurityLog.record(SecurityEvent.MFA_ON, request, user)
        return self.make_backup_codes(user)

    @staticmethod
    def disable(user, by=None, request=None) -> None:
        """Turn MFA off (by the user or by a Super Admin)."""
        user.mfa_enabled = False
        user.set_mfa_secret("")
        user.save(update_fields=["_mfa_secret", "mfa_enabled"])
        user.backup_codes.all().delete()
        SecurityLog.record(SecurityEvent.MFA_OFF, request, user, details=f"by {getattr(by, 'username', user.username)}")

    @staticmethod
    def required_for(user) -> bool:
        """True when this user must set up MFA before using the app."""
        cfg = SystemSettings.load()
        return cfg.force_mfa_for_admins and user.role in ("super_admin", "school_admin") and not user.mfa_enabled


class ImpersonationService:
    """Super Admin "Login as" another user for testing and support (FR-06)."""

    @staticmethod
    def start(request, target, reason: str) -> ImpersonationSession:
        """Switch the session to ``target``; remember the Super Admin."""
        admin = request.user
        if not admin.is_super_admin or request.session.get(IMPERSONATOR_KEY):
            raise AccessDeniedError("Only a Super Admin can use Login as.")
        if target.is_super_admin:
            raise AccessDeniedError("You cannot log in as another Super Admin.")
        if target.pk == admin.pk:
            raise ValidationError("You are already this user.")
        reason = (reason or "").strip()
        if len(reason) < 5:
            raise ValidationError("Please write a short reason (at least 5 characters).")
        record = ImpersonationSession.objects.create(admin=admin, target=target, reason=reason[:200])
        SecurityLog.record(SecurityEvent.IMPERSONATE_START, request, admin, details=f"as {target.username}: {reason}")
        login(request, target, backend="django.contrib.auth.backends.ModelBackend")
        request.session[IMPERSONATOR_KEY] = admin.pk
        request.session[IMPERSONATION_KEY] = record.pk
        return record

    @staticmethod
    def stop(request):
        """Return to the Super Admin's own account."""
        admin_id = request.session.get(IMPERSONATOR_KEY)
        record_id = request.session.get(IMPERSONATION_KEY)
        if not admin_id:
            return None
        admin = User.objects.get(pk=admin_id)
        target_name = request.user.username
        ImpersonationSession.objects.filter(pk=record_id).update(ended_at=timezone.now())
        login(request, admin, backend="django.contrib.auth.backends.ModelBackend")
        request.session.pop(IMPERSONATOR_KEY, None)
        request.session.pop(IMPERSONATION_KEY, None)
        SecurityLog.record(SecurityEvent.IMPERSONATE_STOP, request, admin, details=f"was {target_name}")
        return admin

    @staticmethod
    def impersonator(request):
        """The Super Admin behind the current session, or None."""
        admin_id = request.session.get(IMPERSONATOR_KEY)
        return User.objects.filter(pk=admin_id).first() if admin_id else None


class UserService:
    """Create and manage users (FR-03, FR-04)."""

    @staticmethod
    def make_username(first: str, last: str) -> str:
        """first.last in lower case; adds 2, 3 … if the name is taken."""
        base = re.sub(r"[^a-z0-9.]", "", f"{first}.{last}".lower().replace(" ", "")) or "user"
        name, n = base, 2
        while User.objects.filter(username=name).exists():
            name, n = f"{base}{n}", n + 1
        return name

    @transaction.atomic
    def create_user(
        self, *, first_name, last_name, role, password, school=None, email="", by=None, username=None, **extra
    ):
        """Create a user with a checked password."""
        from django.contrib.auth.password_validation import validate_password  # pylint: disable=import-outside-toplevel
        from django.core.exceptions import ValidationError as DjangoError  # pylint: disable=import-outside-toplevel

        username = username or self.make_username(first_name, last_name)
        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            school=school,
            email=email,
            **extra,
        )
        try:
            validate_password(password, user)
        except DjangoError as exc:
            raise ValidationError(" ".join(exc.messages)) from exc
        user.set_password(password)
        user.save()
        AuditService.log(by, "user_created", username, details=f"role={role}")
        return user

    def create_temporary(self, *, role, school=None, by=None, minutes=None) -> tuple:
        """Make a temporary account that stops working after the set minutes. Returns (user, password)."""
        minutes = minutes or SystemSettings.load().temp_account_minutes
        password = "Temp" + secrets.token_hex(3) + "9"
        user = self.create_user(
            first_name="Temporary",
            last_name=secrets.token_hex(2),
            role=role,
            school=school,
            password=password,
            by=by,
            is_temporary=True,
            expires_at=timezone.now() + timedelta(minutes=minutes),
        )
        return user, password

    @staticmethod
    def reset_password(user, new_password: str, by=None, request=None) -> None:
        """Super Admin or School Admin sets a new password; the user must change it next time."""
        from django.contrib.auth.password_validation import validate_password  # pylint: disable=import-outside-toplevel
        from django.core.exceptions import ValidationError as DjangoError  # pylint: disable=import-outside-toplevel

        try:
            validate_password(new_password, user)
        except DjangoError as exc:
            raise ValidationError(" ".join(exc.messages)) from exc
        user.set_password(new_password)
        user.must_change_password = True
        user.save()
        SecurityLog.record(SecurityEvent.PASSWORD_RESET, request, user, details=f"by {getattr(by, 'username', '')}")

    @staticmethod
    def set_active(user, active: bool, by=None) -> None:
        """Switch an account on or off."""
        if user.is_super_admin and not active and User.objects.filter(role="super_admin", is_active=True).count() <= 1:
            raise ValidationError("You cannot switch off the last Super Admin.")
        user.is_active = active
        user.save(update_fields=["is_active"])
        AuditService.log(by, "user_status", user.username, not active, active)

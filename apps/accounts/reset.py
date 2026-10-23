"""
reset.py - "Forgot password?" by email, WhatsApp or Viber
=========================================================

Owner: Anish Shrestha (task A-21) with Jihe Qi (messaging adapters)

* The page always shows the SAME message, so nobody can find out which
  usernames exist (no account enumeration).
* The link uses Django's signed one-time token and works for 1 hour.
* At most 3 requests per account per hour; every request is in the security log.
* Students do not have email: their teacher or School Admin resets them.
* WhatsApp and Viber only appear when the Super Admin switched them on in
  Integrations (and the feature switch is on).
"""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.core.exceptions import IntegrationError
from apps.core.models import FeatureSwitch
from apps.security.models import SecurityEvent
from apps.security.services import SecurityLog

User = get_user_model()
MAX_PER_HOUR = 3
GENERIC_MESSAGE = (
    "If an account matches, we sent a reset link. It works for 1 hour. "
    "Students: please ask your teacher to reset your password."
)


class PasswordResetService:
    """Request a reset link and check it."""

    @staticmethod
    def channels() -> list[tuple[str, str]]:
        """Email always, plus WhatsApp and Viber when they are switched on."""
        from apps.integrations.services import IntegrationService  # pylint: disable=import-outside-toplevel

        service, out = IntegrationService(), [("email", "Email")]
        for name, label in (("whatsapp", "WhatsApp"), ("viber", "Viber")):
            if FeatureSwitch.is_on(name) and service.enabled(name):
                out.append((name, label))
        return out

    @staticmethod
    def _find(identifier: str):
        identifier = (identifier or "").strip()
        if not identifier:
            return None
        return User.objects.filter(Q(username__iexact=identifier) | Q(email__iexact=identifier), is_active=True).first()

    @staticmethod
    def _too_many(user) -> bool:
        since = timezone.now() - timedelta(hours=1)
        return (
            SecurityEvent.objects.filter(user=user, event="password_reset_requested", created_at__gte=since).count()
            >= MAX_PER_HOUR
        )

    @staticmethod
    def link(request, user) -> str:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return request.build_absolute_uri(
            reverse("accounts:reset_confirm", args=[uid, default_token_generator.make_token(user)])
        )

    def request_reset(self, request, identifier: str, channel: str) -> str:
        """Send a link if possible. Always returns the same message."""
        user = self._find(identifier)
        if user is None or user.is_student or user.is_guest or self._too_many(user):
            SecurityLog.record(
                "password_reset_ignored",
                request,
                user,
                username=identifier[:150],
                details="no match, student/guest or too many requests",
            )
            return GENERIC_MESSAGE
        SecurityLog.record("password_reset_requested", request, user, details=f"via {channel}")
        url = self.link(request, user)
        name = user.first_name or user.username
        if channel == "email" and user.email:
            from apps.emails.services import EmailService  # pylint: disable=import-outside-toplevel

            EmailService().send_template("password_reset", user.email, {"name": name, "link": url})
        elif channel in dict(self.channels()) and channel != "email" and user.phone:
            from apps.integrations.services import IntegrationService  # pylint: disable=import-outside-toplevel

            try:
                IntegrationService().adapter(channel).send(
                    user.phone, f"Kia ora {name}, reset your CyberQuest " f"password here (1 hour): {url}"
                )
            except IntegrationError as exc:
                SecurityLog.record("password_reset_failed", request, user, details=f"{channel}: {exc.message}")
        return GENERIC_MESSAGE

    @staticmethod
    def check(uidb64: str, token: str):
        """Return the user for a valid link, else None."""
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)), is_active=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return None
        return user if default_token_generator.check_token(user, token) else None

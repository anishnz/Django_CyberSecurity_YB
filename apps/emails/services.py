"""
services.py - Send emails from templates (Gmail SMTP or the local backend)
==========================================================================

Owner: Rajneesh Kumar (task R-14)

* If the Gmail integration is switched on, emails go through smtp.gmail.com with
  the App Password from the encrypted vault. Otherwise Django's normal email
  backend is used (console in development, memory in tests) – nothing breaks.
* Every attempt is written to EmailLog. Emails never stop the main action: a
  failure is logged, not raised.
* Bulk emails skip people who unsubscribed and add an unsubscribe link.
"""

from __future__ import annotations

import logging
import string
import uuid

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.urls import reverse

from .defaults import DEFAULT_TEMPLATES
from .models import EmailLog, EmailTemplate, Unsubscribe

logger = logging.getLogger("cyberquest")
BULK_LIMIT = 400  # Gmail allows about 500 a day on a normal account


class _SafeDict(dict):
    """Unknown {placeholders} stay as they are instead of crashing."""

    def __missing__(self, key):
        return "{" + key + "}"


def render_text(text: str, ctx: dict) -> str:
    return string.Formatter().vformat(text, (), _SafeDict({k: str(v) for k, v in ctx.items()}))


class EmailService:
    """Templates in, emails out."""

    @staticmethod
    def ensure_defaults() -> int:
        """Create the starting email templates that do not exist yet. Returns how many were made."""
        made = 0
        for key, (name, audience, subject, body) in DEFAULT_TEMPLATES.items():
            _, created = EmailTemplate.objects.get_or_create(
                key=key, defaults={"name": name, "audience": audience, "subject": subject, "body": body}
            )
            made += created
        return made

    def template(self, key: str) -> EmailTemplate | None:
        tpl = EmailTemplate.objects.filter(key=key).first()
        if tpl is None and key in DEFAULT_TEMPLATES:
            self.ensure_defaults()
            tpl = EmailTemplate.objects.filter(key=key).first()
        return tpl if tpl and tpl.is_active else None

    @staticmethod
    def _connection():
        """Gmail SMTP when switched on, otherwise the normal backend. Returns (connection, from, via)."""
        from apps.integrations.services import IntegrationService  # pylint: disable=import-outside-toplevel

        service = IntegrationService()
        if service.enabled("gmail"):
            gmail = service.adapter("gmail")
            conn = get_connection(
                "django.core.mail.backends.smtp.EmailBackend",
                host=gmail.extra["smtp_host"],
                port=int(gmail.extra["smtp_port"]),
                username=gmail.extra["address"],
                password=gmail.secret,
                use_tls=True,
                timeout=15,
            )
            return conn, f"{gmail.extra['sender_name']} <{gmail.extra['address']}>", "gmail"
        return get_connection(), settings.DEFAULT_FROM_EMAIL, "local"

    def send(
        self, to: str, subject: str, body: str, template_key: str = "", batch: str = "", connection=None
    ) -> EmailLog:
        """Send one email and write it to the email log. Never raises: a failure is logged."""
        conn, sender, via = connection or self._connection()
        try:
            EmailMessage(subject[:200], body, sender, [to], connection=conn).send()
            return EmailLog.objects.create(
                to=to, subject=subject[:200], template_key=template_key, status=EmailLog.SENT, via=via, batch=batch
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Email to %s failed: %s", to, exc)
            return EmailLog.objects.create(
                to=to,
                subject=subject[:200],
                template_key=template_key,
                status=EmailLog.FAILED,
                via=via,
                error=str(exc)[:300],
                batch=batch,
            )

    def send_template(self, key: str, to: str, ctx: dict) -> EmailLog | None:
        tpl = self.template(key)
        if tpl is None or not to:
            return None
        return self.send(to, render_text(tpl.subject, ctx), render_text(tpl.body, ctx), key)

    # ------------------------------------------------------------- bulk
    @staticmethod
    def unsubscribe_link(email: str, base_url: str = "") -> str:
        row, _ = Unsubscribe.objects.get_or_create(email=email.lower())
        return base_url + reverse("emails:unsubscribe", args=[row.token])

    @staticmethod
    def recipients(audience: str, school=None) -> list[dict]:
        """People a bulk email would go to (opted-in parents, or active staff)."""
        from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel
        from apps.schools.models import StudentProfile  # pylint: disable=import-outside-toplevel

        blocked = set(Unsubscribe.objects.filter(unsubscribed=True).values_list("email", flat=True))
        out = []
        if audience == "parents":
            qs = (
                StudentProfile.objects.filter(parent_opt_in=True)
                .exclude(parent_email="")
                .select_related("user", "user__school")
            )
            if school:
                qs = qs.filter(user__school=school)
            for p in qs:
                out.append(
                    {
                        "email": p.parent_email,
                        "name": p.parent_name or "whānau",
                        "student": p.user.first_name,
                        "school": p.user.school.name if p.user.school else "",
                    }
                )
        else:
            role = {"teachers": "teacher", "admins": "school_admin"}.get(audience, "teacher")
            qs = get_user_model().objects.filter(role=role, is_active=True).exclude(email="").select_related("school")
            if school:
                qs = qs.filter(school=school)
            for u in qs:
                out.append(
                    {"email": u.email, "name": u.first_name or u.username, "school": u.school.name if u.school else ""}
                )
        seen, unique = set(), []
        for r in out:
            if r["email"].lower() not in blocked and r["email"].lower() not in seen:
                seen.add(r["email"].lower())
                unique.append(r)
        return unique[:BULK_LIMIT]

    def bulk_send(
        self, tpl: EmailTemplate, recipients: list[dict], extra: dict, base_url: str = ""
    ) -> tuple[str, int, int]:
        """Send one template to many people. Returns (batch id, sent, failed)."""
        batch, sent, failed = uuid.uuid4().hex[:8], 0, 0
        connection = self._connection()
        for r in recipients:
            ctx = {**extra, **r, "unsubscribe": self.unsubscribe_link(r["email"], base_url)}
            log = self.send(
                r["email"], render_text(tpl.subject, ctx), render_text(tpl.body, ctx), tpl.key, batch, connection
            )
            sent, failed = sent + (log.status == EmailLog.SENT), failed + (log.status == EmailLog.FAILED)
        return batch, sent, failed

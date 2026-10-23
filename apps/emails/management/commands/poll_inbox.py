"""
poll_inbox - Read new support emails from Gmail (IMAP), open tickets, auto-reply
===============================================================================

Owner: Rajneesh Kumar (task R-15)

Run it every few minutes (Windows Task Scheduler or cron):
    python manage.py poll_inbox

* Only runs when the Gmail integration and the "Email auto-reply" switch are on.
* Each unread email becomes a ticket; the ticket service sends the
  "ticket_opened" auto-reply with the ticket number.
* Replies from our own address and "no-reply" senders are skipped (no loops).
"""
from __future__ import annotations

import email
from email.header import decode_header, make_header
from email.utils import parseaddr

from django.core.management.base import BaseCommand

from apps.core.models import FeatureSwitch
from apps.helpdesk.services import TicketService
from apps.integrations.services import IntegrationService

MAX_PER_RUN = 25


def _text(value) -> str:
    return str(make_header(decode_header(value or "")))


def plain_body(msg) -> str:
    """The plain-text part of an email (first 5000 characters)."""
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.get_content_type() == "text/plain" and not part.get_filename():
            payload = part.get_payload(decode=True) or b""
            return payload.decode(part.get_content_charset() or "utf-8", errors="replace")[:5000]
    return ""


def should_skip(sender: str, own_address: str, msg) -> bool:
    low = sender.lower()
    return (not low or low == own_address.lower() or "no-reply" in low or "noreply" in low or "mailer-daemon" in low
            or (msg.get("Auto-Submitted", "no").lower() != "no"))


class Command(BaseCommand):
    help = "Turn unread support emails into tickets and send an automatic reply."

    def handle(self, *args, **opts):
        service = IntegrationService()
        if not (service.enabled("gmail") and FeatureSwitch.is_on("email_auto_reply")):
            self.stdout.write("Gmail or Email auto-reply is switched off – nothing to do.")
            return
        gmail = service.adapter("gmail")
        box = gmail.imap()
        made = 0
        try:
            box.select("INBOX")
            _, data = box.search(None, "UNSEEN")
            for num in (data[0].split() if data and data[0] else [])[:MAX_PER_RUN]:
                _, fetched = box.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(fetched[0][1])
                name, sender = parseaddr(msg.get("From", ""))
                if should_skip(sender, gmail.extra["address"], msg):
                    continue
                TicketService().from_email(sender, _text(name), _text(msg.get("Subject"))[:150], plain_body(msg))
                made += 1
        finally:
            box.logout()
        self.stdout.write(self.style.SUCCESS(f"{made} ticket(s) created from email."))

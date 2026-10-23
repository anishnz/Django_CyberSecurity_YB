"""test_emails.py - Templates, placeholders, bulk preview/send, unsubscribe, inbox rules. Owner: Jihe Qi (QA)."""
from email.message import EmailMessage as PyEmail

import pytest
from django.core import mail

from apps.emails.management.commands.poll_inbox import plain_body, should_skip
from apps.emails.models import EmailLog, EmailTemplate, Unsubscribe
from apps.emails.services import EmailService, render_text

pytestmark = pytest.mark.django_db


def test_default_templates_seeded():
    assert EmailTemplate.objects.filter(key="ticket_opened").exists()
    assert EmailTemplate.objects.filter(audience="parents").count() >= 2


def test_unknown_placeholders_do_not_crash():
    assert render_text("Hi {name}, {missing}", {"name": "Aroha"}) == "Hi Aroha, {missing}"


def test_send_template_logs_local_email():
    mail.outbox = []
    log = EmailService().send_template("ticket_reply", "x@example.org", {"name": "Tama", "ticket": "CQ-0099"})
    assert log.status == EmailLog.SENT and log.via == "local" and "CQ-0099" in mail.outbox[0].subject


def test_bulk_parents_only_opted_in_and_skips_unsubscribed(user):
    school = user("tama.ngata").school
    people = EmailService.recipients("parents", school)
    assert people and all(p["email"].startswith("parent.") for p in people)
    Unsubscribe.objects.create(email=people[0]["email"], unsubscribed=True)
    assert len(EmailService.recipients("parents", school)) == len(people) - 1


def test_bulk_send_adds_unsubscribe_link(user):
    mail.outbox = []
    school = user("tama.ngata").school
    tpl = EmailTemplate.objects.get(key="teacher_notice")
    people = EmailService.recipients("teachers", school)
    _, sent, failed = EmailService().bulk_send(tpl, people, {"message": "Cyber Smart Week"}, "http://testserver")
    assert sent == len(people) and failed == 0 and "/email/unsubscribe/" in mail.outbox[0].body


def test_bulk_page_preview_then_send(login):
    client = login("admin.brightstar")
    tpl = EmailTemplate.objects.get(key="parent_notice")
    r = client.post("/email/bulk/", {"template": tpl.pk, "message": "Assembly on Friday."})
    assert r.status_code == 200 and b"This will send" in r.content
    r = client.post("/email/bulk/", {"template": tpl.pk, "message": "Assembly on Friday.", "confirmed": "yes"})
    assert r.status_code == 302 and EmailLog.objects.filter(template_key="parent_notice").exists()


def test_unsubscribe_needs_post():
    row = Unsubscribe.objects.create(email="p@example.org")
    from django.test import Client  # pylint: disable=import-outside-toplevel
    client = Client()
    client.get(f"/email/unsubscribe/{row.token}/")
    row.refresh_from_db()
    assert not row.unsubscribed
    client.post(f"/email/unsubscribe/{row.token}/", {"action": "unsubscribe"})
    row.refresh_from_db()
    assert row.unsubscribed


def test_inbox_skips_loops_and_reads_plain_text():
    msg = PyEmail()
    msg["From"], msg["Subject"] = "Parent <p@example.org>", "Help"
    msg.set_content("My child cannot log in.")
    assert not should_skip("p@example.org", "support@gmail.com", msg)
    assert should_skip("support@gmail.com", "support@gmail.com", msg)
    assert should_skip("no-reply@bank.co.nz", "support@gmail.com", msg)
    assert "cannot log in" in plain_body(msg)

"""test_helpdesk.py - Tickets: routing, visibility, state machine, attachments, report a question.

Owner: Jihe Qi (QA).
"""

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.exceptions import AccessDeniedError, UploadRejectedError, ValidationError
from apps.helpdesk.models import Ticket
from apps.helpdesk.services import TicketService
from apps.learning.models import Question

pytestmark = pytest.mark.django_db
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_ticket_number_and_routing_student_to_teachers(user):
    tama = user("tama.ngata")
    t = TicketService().create(title="Cannot open level", description="The level button does nothing.", requester=tama)
    assert t.number.startswith("CQ-") and t.school == tama.school and t.sla_due
    handlers = TicketService.handlers_for(tama)
    assert user("sione.faleolo").pk in handlers and all(u != tama.pk for u in handlers)


def test_website_ticket_goes_to_super_admin_and_auto_replies():
    mail.outbox = []
    t = TicketService().create(
        title="Pricing question",
        description="Do kura get a discount?",
        category="contact",
        email="visitor@example.org",
        name="Visitor",
    )
    assert t.requester is None and mail.outbox and "CQ-" in mail.outbox[0].subject
    assert TicketService.handlers_for(None)


def test_visibility_between_schools(user):
    tama, bikash = user("tama.ngata"), user("bikash.thapa")
    t = TicketService().create(title="Help me please", description="Something is wrong here.", requester=tama)
    with pytest.raises(AccessDeniedError):
        TicketService().check_view(bikash, t)
    with pytest.raises(AccessDeniedError):
        TicketService().check_view(user("sita.sharma"), t)
    TicketService().check_view(user("sione.faleolo"), t)
    TicketService().check_view(user("superadmin"), t)


def test_state_machine_blocks_bad_moves(user):
    t = TicketService().create(
        title="Timer issue", description="Timer stops on question 3.", requester=user("tama.ngata")
    )
    sione = user("sione.faleolo")
    with pytest.raises(ValidationError):
        TicketService().move(t, Ticket.WAITING, sione)  # open -> waiting is not allowed
    TicketService().move(t, Ticket.IN_PROGRESS, sione)
    TicketService().move(t, Ticket.RESOLVED, sione)
    assert t.resolved_at is not None and t.history.count() == 2


def test_student_cannot_add_internal_note_or_move(user):
    tama = user("tama.ngata")
    t = TicketService().create(title="Question wrong", description="Two answers look right.", requester=tama)
    with pytest.raises(AccessDeniedError):
        TicketService().comment(t, tama, "secret note", internal=True)
    with pytest.raises(AccessDeniedError):
        TicketService().move(t, Ticket.RESOLVED, tama)
    TicketService().move(t, Ticket.CLOSED, tama)  # the requester may close their own ticket


def test_requester_reply_reopens_waiting_ticket(user):
    tama, sione = user("tama.ngata"), user("sione.faleolo")
    t = TicketService().create(title="Login trouble", description="Password does not work.", requester=tama)
    TicketService().move(t, Ticket.IN_PROGRESS, sione)
    TicketService().move(t, Ticket.WAITING, sione)
    TicketService().comment(t, tama, "I tried again, still broken.")
    t.refresh_from_db()
    assert t.status == Ticket.IN_PROGRESS


def test_attachment_rules(user):
    tama = user("tama.ngata")
    ok = SimpleUploadedFile("shot.png", PNG, content_type="image/png")
    t = TicketService().create(title="Screen shot", description="See the attached picture.", requester=tama, files=[ok])
    assert t.comments.first().attachments.count() == 1
    bad = SimpleUploadedFile("photo.jpg", b"MZ\x90\x00" + b"\x00" * 64, content_type="image/jpeg")  # a renamed .exe
    with pytest.raises(UploadRejectedError):
        TicketService().create(title="Bad file", description="This file is not a picture.", requester=tama, files=[bad])


def test_report_question_page(login):
    q = Question.objects.approved().first()
    client = login("tama.ngata")
    assert client.get(f"/tickets/report-question/{q.pk}/").status_code == 200
    r = client.post(f"/tickets/report-question/{q.pk}/", {"note": "Two answers look right."})
    assert r.status_code == 302 and Ticket.objects.filter(question=q, category="content").exists()


def test_ticket_pages_for_each_role(login):
    for name in ("superadmin", "admin.brightstar", "sione.faleolo", "tama.ngata"):
        client = login(name)
        assert client.get("/tickets/").status_code == 200
        assert client.get("/tickets/new/").status_code == 200
    client = login("tama.ngata")
    r = client.post(
        "/tickets/new/",
        {"title": "Need help", "category": "quiz", "priority": "normal", "description": "My quiz will not start."},
    )
    assert r.status_code == 302
    assert client.get(r["Location"]).status_code == 200


def test_demo_tickets_loaded():
    assert Ticket.objects.count() >= 6 and Ticket.objects.filter(category="contact", requester__isnull=True).exists()

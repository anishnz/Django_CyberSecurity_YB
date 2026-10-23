"""test_sprint4_features.py - Help centre, announcements, AI drafts, media, password reset, display.

Owner: Jihe Qi (QA).
"""

import re

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.ai_assistant.models import AIDraft
from apps.ai_assistant.services import AIDraftService, parse_question, scrub
from apps.announcements.services import AnnouncementService
from apps.core.exceptions import AccessDeniedError, ValidationError
from apps.helpcentre.services import HelpService
from apps.learning.models import LearningTopic
from apps.medialib.models import MediaFile, VideoEmbed
from apps.medialib.services import MediaService
from apps.security.models import SecurityEvent

pytestmark = pytest.mark.django_db
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


# ------------------------------------------------------------ help centre
def test_explain_this_page_finds_article(login):
    assert HelpService.for_page("helpdesk:ticket_list", "student").slug == "tickets"
    page = login("tama.ngata").get("/tickets/")
    assert b"Explain this page" in page.content and b"Tickets (Tautoko)" in page.content


def test_help_articles_filtered_by_role():
    assert not HelpService.for_role("student").filter(slug="users-and-login-as").exists()
    assert HelpService.for_role("super_admin").filter(slug="users-and-login-as").exists()


def test_ai_explain_works_for_guests_offline():
    r = Client().post("/ai/explain/", {"page": "helpdesk:ticket_list", "question": "how do I add a screenshot?"})
    assert r.status_code == 200 and b"Helper answer" in r.content


# ----------------------------------------------------------- announcements
def test_announcement_audience(user):
    student, teacher, other = user("tama.ngata"), user("sione.faleolo"), user("bikash.thapa")

    def titles(u):
        return set(AnnouncementService.visible_to(u).values_list("title", flat=True))

    assert "Year 7 exam on Friday" in titles(student) and "New Level 4 topics" not in titles(student)
    assert "New Level 4 topics" in titles(teacher) and "Year 7 exam on Friday" not in titles(teacher)
    assert "Year 7 exam on Friday" not in titles(other) and "Cyber Smart Week" in titles(other)


def test_only_admins_post(login):
    assert login("sione.faleolo").get("/announcements/new/").status_code == 403
    assert login("admin.brightstar").get("/announcements/new/").status_code == 200


# ---------------------------------------------------------------- AI drafts
def test_scrub_removes_names_and_emails():
    out = scrub("Tama Ngata emailed tama@example.org about phishing")
    assert "Tama" not in out and "@" not in out


def test_parse_question_format():
    data = parse_question("Question: Is this safe?\nA: Yes\nB: No\nAnswer: B\nFeedback: Ask an adult.")
    assert data["answer"] == "B" and set(data["options"]) == {"A", "B"}
    with pytest.raises(ValidationError):
        parse_question("just some text")


def test_two_approvals_then_publish(user):
    sione, jane = user("sione.faleolo"), user("jane.wilson")
    topic = LearningTopic.objects.filter(level__number=1).first()
    draft = AIDraftService().create(sione, AIDraft.QUESTION, "fake prize messages", topic)
    assert draft.provider.startswith("Offline") and draft.status == AIDraft.DRAFT
    draft.needs_cultural_check = True
    draft.save()
    AIDraftService.approve(sione, draft, "teacher")
    assert draft.status == AIDraft.DRAFT  # still waiting for the Kaiārahi
    with pytest.raises(AccessDeniedError):
        AIDraftService.approve(sione, draft, "cultural")
    AIDraftService.approve(jane, draft, "cultural")
    assert draft.status == AIDraft.APPROVED
    question = AIDraftService().publish_question(sione, draft)
    assert question.school == sione.school and question.options.filter(is_correct=True).count() == 1


def test_editing_resets_approvals(user):
    draft = AIDraft.objects.filter(status=AIDraft.APPROVED).first()
    AIDraftService.edit(user("sione.faleolo"), draft, draft.text + " Kia ora whānau.", False)
    assert draft.status == AIDraft.DRAFT and draft.teacher_approved_by is None and draft.needs_cultural_check


def test_students_cannot_open_ai_pages(login):
    assert login("tama.ngata").get("/ai/drafts/").status_code == 403
    assert login("sione.faleolo").get("/ai/drafts/").status_code == 200


# ------------------------------------------------------------------- media
def test_cultural_media_hidden_until_checked(user):
    sione, jane, tama = user("sione.faleolo"), user("jane.wilson"), user("tama.ngata")
    topic = LearningTopic.objects.filter(level__number=1).first()
    m = MediaService.upload(
        sione,
        {
            "kind": "image",
            "title": "Marae poster",
            "description": "",
            "alt_text": "poster",
            "topic": topic,
            "needs_cultural_check": True,
            "is_published": True,
        },
        SimpleUploadedFile("p.png", PNG, content_type="image/png"),
    )
    assert m not in MediaService.for_topic(topic, tama)[0]
    MediaService.cultural_approve(jane, m)
    assert m in MediaService.for_topic(topic, tama)[0]


def test_youtube_and_media_pages(login, user):
    client = login("sione.faleolo")
    assert client.get("/media-library/").status_code == 200
    client.post("/media-library/video/", {"title": "Spot the scam", "url": "https://youtu.be/dQw4w9WgXcQ"})
    assert VideoEmbed.objects.filter(
        title="Spot the scam", video_id="dQw4w9WgXcQ", school=user("sione.faleolo").school
    ).exists()
    r = client.post(
        "/media-library/upload/",
        {
            "kind": "image",
            "title": "Bad",
            "is_published": "on",
            "file": SimpleUploadedFile("x.png", b"MZ\x90\x00evil", content_type="image/png"),
        },
    )
    assert r.status_code == 200 and not MediaFile.objects.filter(title="Bad").exists()


# ---------------------------------------------------------- password reset
def _reset_link():
    return re.search(r"http://testserver(/accounts/reset/[^\s]+/)", mail.outbox[-1].body).group(1)


def test_forgot_password_by_email():
    mail.outbox = []
    client = Client()
    r = client.post("/accounts/forgot/", {"identifier": "sione.faleolo", "channel": "email"})
    assert r.status_code == 302 and mail.outbox
    link = _reset_link()
    r = client.post(link, {"new_password": "NewPass@2026x", "confirm": "NewPass@2026x"})
    assert r.status_code == 302
    assert (
        Client().post("/accounts/login/", {"username": "sione.faleolo", "password": "NewPass@2026x"}).status_code == 302
    )
    assert client.get(link).status_code == 400  # one-time link


def test_forgot_password_same_message_and_no_student_reset():
    mail.outbox = []
    a = Client().post("/accounts/forgot/", {"identifier": "nobody.here", "channel": "email"}, follow=True)
    b = Client().post("/accounts/forgot/", {"identifier": "tama.ngata", "channel": "email"}, follow=True)
    assert not mail.outbox and b"If an account matches" in a.content and b"If an account matches" in b.content
    assert SecurityEvent.objects.filter(event="password_reset_ignored").count() >= 2


def test_forgot_password_rate_limit():
    mail.outbox = []
    for _ in range(5):
        Client().post("/accounts/forgot/", {"identifier": "admin.ktm", "channel": "email"})
    assert len(mail.outbox) == 3


# --------------------------------------------------------- display / maps
def test_display_toggles_and_map_link(login, user):
    page = login("superadmin").get(f"/schools/{user('admin.brightstar').school_id}/")
    assert b"Open in Google Maps" in page.content and b'data-display-toggle="dark"' in page.content

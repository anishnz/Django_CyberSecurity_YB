"""
test_website_photos.py - Team photos and meeting photos (Website content page)
==============================================================================

Owner: Jihe Qi (QA) for Dinesh Upreti's task D-14.
"""

from __future__ import annotations

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.website.models import MeetingPhoto, TeamMember

pytestmark = pytest.mark.django_db


def png(name="photo.png") -> SimpleUploadedFile:
    """A tiny real PNG file."""
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (14, 59, 67)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def test_four_team_members_exist_from_migration():
    names = list(TeamMember.objects.values_list("name", flat=True))
    assert names == ["Anish Shrestha", "Rajneesh Kumar", "Dinesh Upreti", "Jihe Qi"]


def test_about_page_shows_team_and_built_in_meeting_photos(client):
    page = client.get("/about/").content.decode()
    assert "Rajneesh Kumar" in page and "img/meetings/meeting_1.jpg" in page


def test_only_super_admin_can_open_manage_page(client, login):
    assert client.get("/website/manage/").status_code == 302  # to login
    assert login("sione.faleolo").get("/website/manage/").status_code == 403
    assert login("superadmin").get("/website/manage/").status_code == 200


def test_upload_team_photo_and_bio(login):
    admin = login("superadmin")
    member = TeamMember.objects.get(name="Jihe Qi")
    r = admin.post(
        f"/website/manage/team/{member.pk}/", {f"m{member.pk}-bio": "QA lead.", f"m{member.pk}-photo": png()}
    )
    assert r.status_code == 302
    member.refresh_from_db()
    assert member.bio == "QA lead." and member.photo.name.startswith("website/team/")
    assert member.image_url in admin.get("/about/").content.decode()


def test_fake_image_is_rejected(login):
    admin = login("superadmin")
    member = TeamMember.objects.get(name="Anish Shrestha")
    fake = SimpleUploadedFile("photo.png", b"MZ not a picture", content_type="image/png")
    admin.post(f"/website/manage/team/{member.pk}/", {f"m{member.pk}-bio": "", f"m{member.pk}-photo": fake})
    member.refresh_from_db()
    assert not member.photo


def test_meeting_photo_upload_shows_in_slider_then_hide_and_delete(login, client):
    admin = login("superadmin")
    r = admin.post(
        "/website/manage/photos/add/",
        {
            "title": "Sprint 2 review",
            "caption": "Demo day",
            "place": "Auckland Central Library",
            "order": 1,
            "image": png(),
        },
    )
    assert r.status_code == 302
    photo = MeetingPhoto.objects.get(title="Sprint 2 review")
    assert "meetingCarousel" in client.get("/about/").content.decode()
    admin.post(f"/website/manage/photos/{photo.pk}/toggle/")
    assert "img/meetings/meeting_1.jpg" in client.get("/about/").content.decode()  # back to the team photos
    admin.post(f"/website/manage/photos/{photo.pk}/delete/")
    assert not MeetingPhoto.objects.filter(pk=photo.pk).exists()

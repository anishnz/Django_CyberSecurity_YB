"""test_website_video_meetings.py - Landing page demo video and the team's meeting photos (work offline).

Owner: Jihe Qi (QA).
"""

from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client

from apps.website.content import TEAM_MEETING_PHOTOS

pytestmark = pytest.mark.django_db
STATIC = Path(settings.BASE_DIR) / "static"


def test_landing_page_plays_the_local_demo_video_with_captions():
    html = Client().get("/").content.decode()
    assert "<video" in html and "video/cyberquest_demo.mp4" in html and "cyberquest_demo_en.vtt" in html
    assert "youtube" not in html.split("<video")[1].split("</video>")[0]  # no internet needed
    for name in ("cyberquest_demo.mp4", "cyberquest_demo_poster.jpg", "cyberquest_demo_en.vtt"):
        assert (STATIC / "video" / name).is_file()


def test_team_meeting_photos_show_until_others_are_uploaded():
    html = Client().get("/about/").content.decode()
    for file, title, _caption, _place in TEAM_MEETING_PHOTOS:
        assert f"img/meetings/{file}" in html and title in html
        assert (STATIC / "img" / "meetings" / file).is_file()
    assert "No meeting photos yet" not in html

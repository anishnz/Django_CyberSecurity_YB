"""test_website_story.py - Our story page: simulated label, community proposals, meetings slider.

Owner: Jihe Qi (QA).
"""

import pytest
from django.test import Client

from apps.website import story

pytestmark = pytest.mark.django_db


def test_story_page_says_it_is_simulated_first():
    html = Client().get("/story/").content.decode()
    assert "Simulated case study." in html
    # the declaration comes before the first chapter, so nobody reads the story as real first
    assert html.index("Simulated case study.") < html.index(story.CHAPTERS[0][1])


def test_story_page_shows_every_proposal_and_friend():
    html = Client().get("/story/").content.decode()
    for _name, _role, said, built in story.PROPOSALS:
        assert said.replace("'", "&#x27;") in html
        assert built.replace("'", "&#x27;") in html
    for name, _role, _job in story.FRIENDS:
        assert name in html
    assert "Simulated role" in html


def test_story_page_has_meetings_slider_section():
    html = Client().get("/story/").content.decode()
    assert 'id="meetings"' in html

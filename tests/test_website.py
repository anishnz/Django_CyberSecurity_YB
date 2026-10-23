"""test_website.py - Landing page: problem, NZ facts with sources, law, solution, features, architecture.

Owner: Jihe Qi (QA).
"""

import pytest
from django.test import Client

from apps.website import content

pytestmark = pytest.mark.django_db


def test_landing_page_has_every_section():
    page = Client().get("/")
    html = page.content.decode()
    assert page.status_code == 200
    for anchor in ("problem", "facts", "ethics-law", "about", "ai", "features", "architecture"):
        assert f'id="{anchor}"' in html
    assert "Born online. Not born safe." in html and "Show the exits before the fire" in html
    assert 'role="img"' in html and "CyberQuest system architecture" in html


def test_every_fact_and_law_has_a_source_link():
    assert all(url.startswith("https://") for *_, url in content.NZ_FACTS)
    assert all(url.startswith("https://") for *_, url in content.NZ_LAWS)


def test_stories_are_marked_as_made_up_and_ai_promise_is_shown():
    html = Client().get("/").content.decode()
    assert content.STORIES_NOTE in html and "AI does not judge or profile children" in html

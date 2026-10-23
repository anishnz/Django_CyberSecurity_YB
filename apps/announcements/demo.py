"""demo.py - Demo announcements (Pānui). Owner: Jihe Qi (test data)."""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model

from apps.core.clock import today
from apps.schools.models import School

from .models import Announcement

User = get_user_model()


def load_demo_announcements() -> int:
    d, boss = today(), User.objects.filter(role="super_admin").first()
    bright = School.objects.get(code="BRIGHTSTAR")
    Announcement.objects.create(title="Cyber Smart Week", body="Cyber Smart Week starts on Monday. Try one practice "
                                "round every day – ka pai!", audience="all", starts_on=d - timedelta(days=2),
                                ends_on=d + timedelta(days=12), is_pinned=True, created_by=boss)
    Announcement.objects.create(title="New Level 4 topics", body="Level 4 now has a topic about AI chatbots and "
                                "keeping personal details private.", audience="staff", starts_on=d - timedelta(days=5),
                                created_by=boss)
    Announcement.objects.create(title="Year 7 exam on Friday", body="Year 7 sits the Level 1 exam on Friday in period 2.",
                                audience="students", school=bright, starts_on=d - timedelta(days=1),
                                ends_on=d + timedelta(days=4),
                                created_by=User.objects.filter(role="school_admin", school=bright).first())
    return 3

"""
clock.py - One place to ask "what day is it?"
=============================================

Owner: Anish Shrestha. Tests can fix the date with settings.CYBERQUEST["FIXED_TODAY"]
so licence and expiry tests give the same result every day.
"""
from __future__ import annotations

from datetime import date

from django.conf import settings
from django.utils import timezone


def today() -> date:
    """Today's date in New Zealand time (or the fixed test date)."""
    fixed = settings.CYBERQUEST.get("FIXED_TODAY")
    return date.fromisoformat(fixed) if fixed else timezone.localdate()


def now():
    """Current date and time (timezone aware)."""
    return timezone.now()

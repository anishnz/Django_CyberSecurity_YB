"""
conftest.py - Shared test fixtures
==================================

Owner: Jihe Qi (QA Lead, task J-01)

* The demo data is loaded ONCE per test run (session) with ``seed_demo`` and
  every test runs inside a transaction that is rolled back, so tests never
  affect each other.
* The date is fixed to 2026-10-06 so licence tests give the same result every day.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import Client

PASSWORDS = {
    "superadmin": "Everest@2026",
    "admin.brightstar": "Admin@2026",
    "admin.ktm": "Admin@2026",
    "admin.tuivalley": "Admin@2026",
    "sione.faleolo": "Teacher@2026",
    "sita.sharma": "Teacher@2026",
    "tama.ngata": "Kiaora@2026",
    "ella.johnson": "Kiaora@2026",
    "ruby.chen": "Kiaora@2026",
    "bikash.thapa": "Namaste@2026",
    "demo_guest": "Guest@2026",
}


@pytest.fixture(scope="session", autouse=True)
def fixed_date():
    settings.CYBERQUEST["FIXED_TODAY"] = "2026-10-06"
    yield
    settings.CYBERQUEST.pop("FIXED_TODAY", None)


@pytest.fixture(scope="session")
def django_db_setup(
    django_db_setup, django_db_blocker, fixed_date
):  # pylint: disable=redefined-outer-name,unused-argument
    """Load reference data and demo data once."""
    with django_db_blocker.unblock():
        call_command("seed_demo", verbosity=0)


@pytest.fixture
def login(db):  # pylint: disable=unused-argument
    """login('tama.ngata') -> logged-in Client (password check goes through the real login view)."""

    def _login(username: str, password: str | None = None) -> Client:
        client = Client()
        response = client.post("/accounts/login/", {"username": username, "password": password or PASSWORDS[username]})
        assert response.status_code == 302, f"login failed for {username}: {response.status_code}"
        return client

    return _login


@pytest.fixture
def user(db):  # pylint: disable=unused-argument
    """user('tama.ngata') -> User object."""
    from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel

    def _get(username: str):
        return get_user_model().objects.get(username=username)

    return _get

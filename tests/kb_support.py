"""kb_support.py - Shared helpers for the Knowledge Base tests (the RAG service is always mocked)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.schools.models import StudentProfile

BASE_DIR = Path(__file__).resolve().parent.parent
CJK = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]")
ROLES = ("student", "teacher", "school_admin", "super_admin", "guest")
STAFF = ("teacher", "school_admin", "super_admin")
# Where apps.kb.services calls requests: patch this to fake the RAG service.
RAG_REQUEST = "apps.kb.services.requests.request"


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, data=None, status=200, bad_json=False):
        self.status_code = status
        self._data = data
        self._bad_json = bad_json

    def json(self):
        if self._bad_json:
            raise ValueError("not json")
        return self._data


def make_user(role: str):
    """One user per role (re-used when asked for twice in the same test)."""
    model = get_user_model()
    user = model.objects.filter(username=f"kb_{role}").first()
    if user is None:
        user = model.objects.create_user(username=f"kb_{role}", password="Test@12345", role=role)
        if role == "student":
            # A signal already created the profile; the family consent lets the student use the site.
            StudentProfile.objects.update_or_create(user=user, defaults={"family_consent": True})
    return user


def client_for(role: str, **kwargs) -> Client:
    """A test client that is logged in as a user with this role."""
    client = Client(**kwargs)
    client.force_login(make_user(role))
    return client


@override_settings(RAG_BASE_URL="http://rag.test:9000", RAG_SERVICE_KEY="secret-key")
class KbTestCase(TestCase):
    """Base class: fixed RAG settings and a few request helpers."""

    def post_json(self, client, name, payload, **kwargs):
        return client.post(reverse(name, **kwargs), json.dumps(payload), content_type="application/json")

    def put_json(self, client, name, payload):
        return client.put(reverse(name), json.dumps(payload), content_type="application/json")

"""
services.py - The only place that talks to the shared knowledge-base (RAG) service
==================================================================================

There is ONE knowledge base for every school. Django decides the user's role here
and the RAG service checks it again. The service address and key come from the
settings RAG_BASE_URL and RAG_SERVICE_KEY (read from .env).
"""

from __future__ import annotations

import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger("cyberquest")

CONNECT_TIMEOUT = 5  # seconds to reach the service
READ_TIMEOUT = 180  # the local model can be slow (quiz questions)

# The RAG service answers with this sentence plus a second-language copy when nothing matches.
NOT_FOUND_EN = "I couldn't find this in the knowledge base."
_CJK = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]")


class RagUnavailable(Exception):
    """The RAG service could not be reached or sent something that is not JSON."""


def role_of(user) -> str:
    """Map CyberQuest roles to the three roles the RAG service understands.

    Guests get student-level access. School admins get teacher-level rights in the
    service; the delete rule for them and for teachers is enforced in apps.kb.api.
    """
    role = getattr(user, "role", "")
    if role == "super_admin":
        return "super_admin"
    if role in ("teacher", "school_admin"):
        return "teacher"
    return "student"


def call_rag(method: str, path: str, role: str, json_body=None, **kwargs) -> tuple[int, object]:
    """Send one request to the RAG service. Returns (status code, decoded JSON).

    Raises RagUnavailable when the service is down, too slow or answers with non-JSON.
    """
    url = f"{settings.RAG_BASE_URL.rstrip('/')}{path}"
    headers = {"X-Service-Key": settings.RAG_SERVICE_KEY or "", "X-User-Role": role}
    try:
        response = requests.request(
            method, url, headers=headers, json=json_body, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), **kwargs
        )
    except requests.RequestException as exc:
        logger.warning("KB service request failed: %s %s (%s)", method, path, type(exc).__name__)
        raise RagUnavailable(str(exc)) from exc
    try:
        data = response.json()
    except ValueError as exc:
        logger.warning("KB service sent a non-JSON reply: %s %s (HTTP %s)", method, path, response.status_code)
        raise RagUnavailable("not JSON") from exc
    return response.status_code, data


def english_answer(answer):
    """Keep the 'nothing found' reply English-only (the service adds a second-language copy)."""
    if isinstance(answer, str) and NOT_FOUND_EN in answer and _CJK.search(answer):
        return NOT_FOUND_EN
    return answer

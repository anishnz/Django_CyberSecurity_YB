"""test_kb_review.py - Safety added when pull request #59 (Knowledge Base) was reviewed.

Owner: Jihe Qi (QA). The RAG service is mocked, as in test_kb_api.py.
"""

from __future__ import annotations

import json
from unittest import mock

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from tests.kb_support import RAG_REQUEST, FakeResponse, client_for

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("clear_cache")]
ANSWER = FakeResponse({"answer": "ok", "sources": []})


@pytest.fixture(name="clear_cache")
def clear_cache_fixture():
    cache.clear()
    yield
    cache.clear()


def ask(client, question):
    return client.post(reverse("kb:api_ask"), json.dumps({"question": question}), content_type="application/json")


@override_settings(RAG_BASE_URL="http://rag.test:9000", RAG_SERVICE_KEY="secret-key")
def test_names_and_emails_are_removed_before_the_ai_sees_the_question(user):
    tama = user("tama.ngata")  # a real (demo) student name in the database
    with mock.patch(RAG_REQUEST, return_value=ANSWER) as fake:
        ask(client_for("teacher"), f"Is {tama.first_name} safe? Mail me at someone@example.org")
    sent = fake.call_args.kwargs["json"]["question"]
    assert tama.first_name not in sent and "someone@example.org" not in sent
    assert "[name]" in sent and "[email]" in sent


@override_settings(RAG_BASE_URL="http://rag.test:9000", RAG_SERVICE_KEY="secret-key")
def test_guests_are_limited_to_10_questions_an_hour():
    client = client_for("guest")
    with mock.patch(RAG_REQUEST, return_value=ANSWER) as fake:
        codes = [ask(client, "What is phishing?").status_code for _ in range(11)]
    assert codes[:10] == [200] * 10 and codes[10] == 429
    assert fake.call_count == 10  # the 11th never reached the AI


@override_settings(RAG_BASE_URL="http://rag.test:9000", RAG_SERVICE_KEY="secret-key")
@pytest.mark.parametrize(
    "name, content",
    [
        ("notes.pdf", b"MZ\x90\x00 a renamed program"),
        ("notes.txt", b"text\x00with a null byte"),
        ("a.md", b"\xff\xfe\xfa"),
    ],
)
def test_upload_content_must_match_its_type(name, content):
    with mock.patch(RAG_REQUEST) as fake:
        response = client_for("teacher").post(reverse("kb:api_documents"), {"file": SimpleUploadedFile(name, content)})
    assert response.status_code == 400 and "does not match its type" in response.json()["detail"]
    fake.assert_not_called()


@override_settings(RAG_BASE_URL="http://rag.test:9000", RAG_SERVICE_KEY="secret-key")
def test_a_real_pdf_header_is_accepted():
    with mock.patch(RAG_REQUEST, return_value=FakeResponse({"doc_id": "a1", "chunks": 1})) as fake:
        response = client_for("teacher").post(
            reverse("kb:api_documents"), {"file": SimpleUploadedFile("ok.pdf", b"%PDF-1.7\n...")}
        )
    assert response.status_code == 200 and fake.called


def test_markdown_marks_are_removed_from_answers():
    from apps.kb.services import plain_text  # pylint: disable=import-outside-toplevel

    text = "## Tips\n- **Never share passwords** [2].\n- Use __strong__ passphrases."
    assert plain_text(text) == "Tips\n- Never share passwords [2].\n- Use strong passphrases."

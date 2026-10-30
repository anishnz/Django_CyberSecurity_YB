"""
test_kb_api.py - Knowledge Base proxy endpoints: wiring, permission matrix, errors
==================================================================================

The RAG service is ALWAYS mocked (``requests.request`` inside apps.kb.services).
"""

from __future__ import annotations

import json
from unittest import mock

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from .kb_support import CJK, RAG_REQUEST, ROLES, STAFF, FakeResponse, KbTestCase, client_for, make_user

RAG = "http://rag.test:9000"


class AskTests(KbTestCase):
    def test_ask_returns_answer_and_sources_and_sends_the_service_headers(self):
        reply = {"answer": "Phishing is a scam [1].", "sources": [{"n": 1, "title": "Guide", "snippet": "abc"}]}
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(reply)) as fake:
            response = self.post_json(client_for("teacher"), "kb:api_ask", {"question": " What is phishing? "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), reply)
        self.assertEqual(fake.call_args.args, ("POST", f"{RAG}/v1/ask"))
        self.assertEqual(fake.call_args.kwargs["headers"], {"X-Service-Key": "secret-key", "X-User-Role": "teacher"})
        self.assertEqual(fake.call_args.kwargs["json"], {"question": "What is phishing?"})

    def test_roles_are_mapped_for_the_service_and_guests_get_student_access(self):
        expected = {
            "student": "student",
            "guest": "student",
            "teacher": "teacher",
            "school_admin": "teacher",
            "super_admin": "super_admin",
        }
        for role, rag_role in expected.items():
            with self.subTest(role=role), mock.patch(RAG_REQUEST, return_value=FakeResponse({"answer": "x"})) as fake:
                response = self.post_json(client_for(role), "kb:api_ask", {"question": "hi"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["sources"], [])
                self.assertEqual(fake.call_args.kwargs["headers"]["X-User-Role"], rag_role)

    def test_empty_or_invalid_question_is_a_400_and_never_reaches_the_service(self):
        client = client_for("student")
        with mock.patch(RAG_REQUEST) as fake:
            for payload in ({}, {"question": "   "}, {"question": 5}, {"question": "x" * 1001}, []):
                with self.subTest(payload=payload):
                    response = self.post_json(client, "kb:api_ask", payload)
                    self.assertEqual(response.status_code, 400)
                    self.assertTrue(response.json()["detail"])
            response = client.post(reverse("kb:api_ask"), "not json", content_type="application/json")
            self.assertEqual(response.status_code, 400)
            fake.assert_not_called()

    def test_nothing_found_answer_is_english_only(self):
        mixed = "I couldn't find this in the knowledge base. / \u77e5\u8bc6\u5e93\u4e2d\u6ca1\u6709\u627e\u5230\u3002"
        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"answer": mixed, "sources": []})):
            data = self.post_json(client_for("student"), "kb:api_ask", {"question": "zzz"}).json()
        self.assertEqual(data["answer"], "I couldn't find this in the knowledge base.")
        self.assertFalse(CJK.search(data["answer"]))

    def test_get_is_not_allowed(self):
        self.assertEqual(client_for("student").get(reverse("kb:api_ask")).status_code, 405)

    def test_anonymous_api_call_gets_json_401(self):
        response = Client().post(reverse("kb:api_ask"), "{}", content_type="application/json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Please sign in again.")

    def test_csrf_token_is_required(self):
        client = client_for("student", enforce_csrf_checks=True)
        with mock.patch(RAG_REQUEST) as fake:
            response = client.post(reverse("kb:api_ask"), "{}", content_type="application/json")
        self.assertEqual(response.status_code, 403)
        fake.assert_not_called()


class ServiceDownTests(KbTestCase):
    def test_service_down_gives_an_english_503_on_every_endpoint(self):
        delete_kwargs = {"kwargs": {"doc_id": "abc123"}}
        cases = [
            ("teacher", "post", "kb:api_ask", {"question": "hi"}, {}),
            ("teacher", "get", "kb:api_documents", None, {}),
            ("teacher", "post", "kb:api_quiz", {"topic": "phishing"}, {}),
            ("school_admin", "delete", "kb:api_document_delete", None, delete_kwargs),
            ("super_admin", "get", "kb:api_model", None, {}),
            ("super_admin", "post", "kb:api_model_test", None, {}),
        ]
        for role, verb, name, payload, extra in cases:
            with self.subTest(endpoint=name), mock.patch(RAG_REQUEST, side_effect=requests.ConnectionError("down")):
                client = client_for(role)
                url = reverse(name, **extra)
                if verb == "post":
                    response = client.post(url, json.dumps(payload or {}), content_type="application/json")
                else:
                    response = getattr(client, verb)(url)
                self.assertEqual(response.status_code, 503)
                self.assertIn("not running right now", response.json()["detail"])

    def test_upload_with_service_down_is_a_503(self):
        with mock.patch(RAG_REQUEST, side_effect=requests.ConnectionError("down")):
            response = client_for("teacher").post(
                reverse("kb:api_documents"), {"file": SimpleUploadedFile("a.txt", b"hello")}
            )
        self.assertEqual(response.status_code, 503)

    def test_timeout_and_non_json_reply_are_handled(self):
        client = client_for("student")
        with mock.patch(RAG_REQUEST, side_effect=requests.Timeout("slow")):
            self.assertEqual(self.post_json(client, "kb:api_ask", {"question": "hi"}).status_code, 503)
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(bad_json=True, status=502)):
            self.assertEqual(self.post_json(client, "kb:api_ask", {"question": "hi"}).status_code, 503)

    def test_a_json_list_from_the_service_is_not_passed_on(self):
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(["unexpected"])):
            response = self.post_json(client_for("student"), "kb:api_ask", {"question": "hi"})
        self.assertEqual(response.status_code, 502)

    def test_service_errors_become_english_messages_without_internals(self):
        client = client_for("student")
        cases = {401: 502, 403: 403, 422: 400, 500: 502, 502: 502}
        for upstream, ours in cases.items():
            reply = FakeResponse({"detail": "Model call failed: Boom: secret"}, status=upstream)
            with self.subTest(upstream=upstream), mock.patch(RAG_REQUEST, return_value=reply):
                response = self.post_json(client, "kb:api_ask", {"question": "hi"})
                self.assertEqual(response.status_code, ours)
                self.assertNotIn("secret", response.json()["detail"])

    def test_super_admin_sees_the_model_error_detail(self):
        reply = FakeResponse({"detail": "Model call failed: ConnectError"}, status=502)
        with mock.patch(RAG_REQUEST, return_value=reply):
            response = self.post_json(client_for("super_admin"), "kb:api_model_test", {})
        self.assertEqual(response.status_code, 502)
        self.assertIn("ConnectError", response.json()["detail"])


class PermissionMatrixTests(KbTestCase):
    """Which roles may call which endpoint. Everybody else gets a JSON 403 and the service is not called."""

    def assert_matrix(self, allowed, make_request, reply):
        for role in ROLES:
            with self.subTest(role=role), mock.patch(RAG_REQUEST, return_value=FakeResponse(reply)) as fake:
                response = make_request(client_for(role))
                if role in allowed:
                    self.assertEqual(response.status_code, 200, response.content)
                else:
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(response["Content-Type"], "application/json")
                    self.assertEqual(response.json()["detail"], "You do not have permission to do this.")
                    fake.assert_not_called()

    def test_ask_is_open_to_every_role(self):
        self.assert_matrix(
            ROLES, lambda c: self.post_json(c, "kb:api_ask", {"question": "hi"}), {"answer": "ok", "sources": []}
        )

    def test_list_documents_is_for_staff(self):
        self.assert_matrix(STAFF, lambda c: c.get(reverse("kb:api_documents")), {"documents": []})

    def test_upload_is_for_staff(self):
        def upload(client):
            return client.post(reverse("kb:api_documents"), {"file": SimpleUploadedFile("a.txt", b"hello")})

        self.assert_matrix(STAFF, upload, {"doc_id": "a1", "chunks": 1})

    def test_quiz_is_for_staff(self):
        payload = {"topic": "phishing", "count": 3, "difficulty": "easy"}
        self.assert_matrix(
            STAFF, lambda c: self.post_json(c, "kb:api_quiz", payload), {"questions": [], "parsed": True}
        )

    def test_delete_is_for_school_admin_and_super_admin_only(self):
        url = reverse("kb:api_document_delete", kwargs={"doc_id": "abc123"})
        self.assert_matrix(("school_admin", "super_admin"), lambda c: c.delete(url), {"deleted": "abc123"})

    def test_model_settings_are_super_admin_only(self):
        self.assert_matrix(("super_admin",), lambda c: c.get(reverse("kb:api_model")), {"display_name": "M"})
        self.assert_matrix(
            ("super_admin",), lambda c: self.put_json(c, "kb:api_model", {"display_name": "M"}), {"display_name": "M"}
        )
        self.assert_matrix(
            ("super_admin",), lambda c: c.post(reverse("kb:api_model_test")), {"ok": True, "reply": "pong"}
        )

    def test_denied_attempt_goes_to_the_security_log(self):
        from apps.security.models import SecurityEvent

        client_for("teacher").delete(reverse("kb:api_document_delete", kwargs={"doc_id": "abc123"}))
        self.assertTrue(SecurityEvent.objects.filter(event="access_denied", username="kb_teacher").exists())


class DocumentTests(KbTestCase):
    def test_list_forwards_to_the_service(self):
        docs = {"documents": [{"doc_id": "a1", "title": "Fees", "tags": "fees", "chunks": 3}]}
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(docs)) as fake:
            response = client_for("teacher").get(reverse("kb:api_documents"))
        self.assertEqual(response.json(), docs)
        self.assertEqual(fake.call_args.args, ("GET", f"{RAG}/v1/documents"))

    def test_upload_forwards_the_file_title_and_tags(self):
        upload = SimpleUploadedFile("fees.md", b"# Fees\nSome text", content_type="text/markdown")
        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"doc_id": "a1", "chunks": 2})) as fake:
            response = client_for("teacher").post(
                reverse("kb:api_documents"), {"file": upload, "title": " Fees 2026 ", "tags": "fees"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"doc_id": "a1", "chunks": 2})
        self.assertEqual(fake.call_args.args, ("POST", f"{RAG}/v1/documents"))
        file_tuple = fake.call_args.kwargs["files"]["file"]
        self.assertEqual((file_tuple[0], file_tuple[1]), ("fees.md", b"# Fees\nSome text"))
        self.assertEqual(fake.call_args.kwargs["data"], {"title": "Fees 2026", "tags": "fees"})
        self.assertIsNone(fake.call_args.kwargs["json"])
        self.assertEqual(fake.call_args.kwargs["headers"]["X-User-Role"], "teacher")

    def test_upload_validation_happens_before_the_service_is_called(self):
        client = client_for("teacher")
        with mock.patch(RAG_REQUEST) as fake:
            response = client.post(reverse("kb:api_documents"), {})
            self.assertEqual((response.status_code, response.json()["detail"]), (400, "Please choose a file to upload."))
            response = client.post(reverse("kb:api_documents"), {"file": SimpleUploadedFile("virus.exe", b"MZ")})
            self.assertEqual(response.status_code, 400)
            self.assertIn("Only PDF, TXT and Markdown", response.json()["detail"])
            fake.assert_not_called()

    def test_too_large_file_is_rejected_with_413(self):
        with mock.patch("apps.kb.api.MAX_UPLOAD_BYTES", 5), mock.patch(RAG_REQUEST) as fake:
            response = client_for("teacher").post(
                reverse("kb:api_documents"), {"file": SimpleUploadedFile("a.txt", b"123456789")}
            )
        self.assertEqual(response.status_code, 413)
        fake.assert_not_called()

    def test_service_rejecting_the_file_shows_its_message(self):
        reply = FakeResponse({"detail": "No readable text found in the document"}, status=400)
        with mock.patch(RAG_REQUEST, return_value=reply):
            response = client_for("teacher").post(
                reverse("kb:api_documents"), {"file": SimpleUploadedFile("a.txt", b"  ")}
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "No readable text found in the document")

    def test_school_admin_and_super_admin_can_delete(self):
        for role in ("school_admin", "super_admin"):
            reply = FakeResponse({"deleted": "abc123"})
            with self.subTest(role=role), mock.patch(RAG_REQUEST, return_value=reply) as fake:
                response = client_for(role).delete(reverse("kb:api_document_delete", kwargs={"doc_id": "abc123"}))
                self.assertEqual(response.json(), {"deleted": "abc123"})
                self.assertEqual(fake.call_args.args, ("DELETE", f"{RAG}/v1/documents/abc123"))

    def test_teacher_delete_is_403_and_the_service_is_not_called(self):
        with mock.patch(RAG_REQUEST) as fake:
            response = client_for("teacher").delete(reverse("kb:api_document_delete", kwargs={"doc_id": "abc123"}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        fake.assert_not_called()

    def test_delete_rejects_odd_document_ids(self):
        with mock.patch(RAG_REQUEST) as fake:
            response = client_for("super_admin").delete(
                reverse("kb:api_document_delete", kwargs={"doc_id": "a b"}),
            )
        self.assertEqual(response.status_code, 400)
        fake.assert_not_called()

    def test_upload_and_delete_are_written_to_the_audit_log(self):
        from apps.core.models import AuditLog

        client = client_for("super_admin")
        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"doc_id": "a1", "chunks": 1})):
            client.post(reverse("kb:api_documents"), {"file": SimpleUploadedFile("a.txt", b"x"), "title": "T"})
        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"deleted": "a1"})):
            client.delete(reverse("kb:api_document_delete", kwargs={"doc_id": "a1"}))
        self.assertTrue(AuditLog.objects.filter(action="kb_document_uploaded", target="T").exists())
        self.assertTrue(AuditLog.objects.filter(action="kb_document_deleted", target="a1").exists())

    def test_demo_guest_cannot_post_to_staff_endpoints(self):
        # The read-only middleware lets /kb/api/ through, so the endpoint itself must answer 403.
        with mock.patch(RAG_REQUEST) as fake:
            response = client_for("guest").post(
                reverse("kb:api_documents"), {"file": SimpleUploadedFile("a.txt", b"x")}
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        fake.assert_not_called()


class QuizAndModelTests(KbTestCase):
    def test_quiz_is_forwarded(self):
        reply = {
            "questions": [{"question": "Q?", "options": ["A. x"], "answer": "A", "explanation": "e"}],
            "parsed": True,
            "sources": [],
        }
        payload = {"topic": " phishing ", "count": "3", "difficulty": "hard"}
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(reply)) as fake:
            response = self.post_json(client_for("teacher"), "kb:api_quiz", payload)
        self.assertEqual(response.json(), reply)
        self.assertEqual(fake.call_args.args, ("POST", f"{RAG}/v1/quiz"))
        self.assertEqual(fake.call_args.kwargs["json"], {"topic": "phishing", "count": 3, "difficulty": "hard"})

    def test_quiz_validation(self):
        client = client_for("teacher")
        bad = [
            {},
            {"topic": ""},
            {"topic": "x" * 301},
            {"topic": "x", "count": 0},
            {"topic": "x", "count": 21},
            {"topic": "x", "count": "abc"},
            {"topic": "x", "difficulty": "insane"},
        ]
        with mock.patch(RAG_REQUEST) as fake:
            for payload in bad:
                with self.subTest(payload=payload):
                    self.assertEqual(self.post_json(client, "kb:api_quiz", payload).status_code, 400)
            fake.assert_not_called()

    def test_quiz_without_material_shows_the_service_message(self):
        reply = FakeResponse({"detail": "No relevant material in the knowledge base; upload some first"}, status=404)
        with mock.patch(RAG_REQUEST, return_value=reply):
            response = self.post_json(client_for("teacher"), "kb:api_quiz", {"topic": "x"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("upload some first", response.json()["detail"])

    def test_quiz_answer_that_could_not_be_parsed_is_passed_on(self):
        reply = {"raw": "Sorry, no JSON", "parsed": False, "sources": []}
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(reply)):
            response = self.post_json(client_for("teacher"), "kb:api_quiz", {"topic": "x"})
        self.assertEqual(response.json(), reply)

    def test_model_settings_can_be_read(self):
        view = {"display_name": "M", "api_key_masked": "******abcd"}
        with mock.patch(RAG_REQUEST, return_value=FakeResponse(view)) as fake:
            response = client_for("super_admin").get(reverse("kb:api_model"))
        self.assertEqual(response.json(), view)
        self.assertEqual(fake.call_args.args, ("GET", f"{RAG}/v1/admin/model"))
        self.assertEqual(fake.call_args.kwargs["headers"]["X-User-Role"], "super_admin")

    def test_model_settings_update_sends_only_filled_in_fields(self):
        body = {"display_name": " New ", "api_key": "", "temperature": "0.5", "max_tokens": "800", "model_id": ""}
        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"display_name": "New"})) as fake:
            response = self.put_json(client_for("super_admin"), "kb:api_model", body)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fake.call_args.args, ("PUT", f"{RAG}/v1/admin/model"))
        self.assertEqual(fake.call_args.kwargs["json"], {"display_name": "New", "temperature": 0.5, "max_tokens": 800})

    def test_model_settings_update_is_audited_without_the_key(self):
        from apps.core.models import AuditLog

        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"display_name": "New"})):
            self.put_json(client_for("super_admin"), "kb:api_model", {"api_key": "sk-very-secret", "model_id": "m1"})
        entry = AuditLog.objects.get(action="kb_model_settings_changed")
        self.assertEqual(entry.target, "api_key, model_id")
        self.assertNotIn("sk-very-secret", f"{entry.target} {entry.details} {entry.new_value}")

    def test_model_settings_reject_bad_numbers(self):
        with mock.patch(RAG_REQUEST) as fake:
            response = self.put_json(client_for("super_admin"), "kb:api_model", {"temperature": "hot"})
        self.assertEqual(response.status_code, 400)
        fake.assert_not_called()

    def test_model_connection_test_is_forwarded(self):
        with mock.patch(RAG_REQUEST, return_value=FakeResponse({"ok": True, "reply": "pong"})) as fake:
            response = client_for("super_admin").post(reverse("kb:api_model_test"))
        self.assertEqual(response.json()["reply"], "pong")
        self.assertEqual(fake.call_args.args, ("POST", f"{RAG}/v1/admin/model/test"))


class SettingsTests(KbTestCase):
    def test_service_address_and_key_are_read_from_settings(self):
        from django.test import override_settings

        with override_settings(RAG_BASE_URL="http://other.test:1234/", RAG_SERVICE_KEY="k2"):
            with mock.patch(RAG_REQUEST, return_value=FakeResponse({"answer": "x"})) as fake:
                self.post_json(client_for("student"), "kb:api_ask", {"question": "hi"})
        self.assertEqual(fake.call_args.args[1], "http://other.test:1234/v1/ask")
        self.assertEqual(fake.call_args.kwargs["headers"]["X-Service-Key"], "k2")

    def test_helper_users_exist(self):
        self.assertEqual(make_user("student").role, "student")

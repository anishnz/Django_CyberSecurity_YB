"""
api.py - JSON endpoints used by the Knowledge Base pages (thin proxy to the RAG service)
========================================================================================

Permissions (checked here AND again by the RAG service):
    * ask ............ every signed-in role (guests get student-level access)
    * list / upload / quiz ... teacher, school admin, super admin
    * delete ......... school admin, super admin (NOT teachers)
    * model settings . super admin only
There is one shared knowledge base for all schools, so nothing here is filtered by school.
Every error is returned as JSON: {"detail": "<English message>"}.
"""

from __future__ import annotations

import json
import re
from functools import wraps

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.core.services import AuditService

from . import services
from .services import RagUnavailable, call_rag, role_of

ALL_ROLES = ("super_admin", "school_admin", "teacher", "student", "guest")
UPLOADERS = ("super_admin", "school_admin", "teacher")
DELETERS = ("super_admin", "school_admin")
SUPER_ONLY = ("super_admin",)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = (".pdf", ".txt", ".md")
DOC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
DIFFICULTIES = ("easy", "medium", "hard")
MODEL_FIELDS = {
    "display_name": str,
    "base_url": str,
    "model_id": str,
    "api_key": str,
    "temperature": float,
    "max_tokens": int,
    "timeout": int,
}


def error(message: str, status: int) -> JsonResponse:
    """A JSON error in the one format the pages understand."""
    return JsonResponse({"detail": message}, status=status)


def kb_api(*roles: str):
    """Allow the endpoint only for these CyberQuest roles. Answers with JSON 401/403, never a redirect."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return error("Please sign in again.", 401)
            if request.user.role not in roles:
                from apps.security.services import SecurityLog  # pylint: disable=import-outside-toplevel

                SecurityLog.record("access_denied", request, request.user, details=f"needs {', '.join(roles)}")
                return error("You do not have permission to do this.", 403)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def _json_body(request) -> dict | None:
    """The JSON object sent by the page, or None when it is missing or broken."""
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _friendly(status: int, data, role: str) -> tuple[str, int]:
    """Turn an error answer of the RAG service into an English message and a status for the browser."""
    detail = data.get("detail") if isinstance(data, dict) else None
    detail = detail if isinstance(detail, str) else ""
    if status == 401:
        return "The knowledge base service refused the connection. Ask the Super Admin to check the service key.", 502
    if status == 403:
        return "You do not have permission to do this.", 403
    if status == 422:
        return "Please check what you typed and try again.", 400
    if status == 413:
        return "That file is too large (20 MB maximum).", 413
    if status >= 500:
        if role == "super_admin" and detail:
            return detail, 502
        return "The AI model did not answer. Please try again in a moment.", 502
    return detail or f"The knowledge base service reported a problem (error {status}).", status


def _forward(request, method: str, path: str, json_body=None, **kwargs) -> JsonResponse:
    """Call the RAG service as the right role and return its answer (or a clear English error)."""
    role = role_of(request.user)
    try:
        status, data = call_rag(method, path, role, json_body=json_body, **kwargs)
    except RagUnavailable:
        return error("The knowledge base service is not running right now. Please try again later.", 503)
    if status >= 400:
        message, out_status = _friendly(status, data, role)
        return error(message, out_status)
    if not isinstance(data, dict):
        return error("The knowledge base service sent an answer the page cannot read.", 502)
    return JsonResponse(data)


@kb_api(*ALL_ROLES)
@require_http_methods(["POST"])
def ask(request):
    """Ask a question; the answer comes with its sources."""
    body = _json_body(request)
    if body is None:
        return error("The request was not valid. Please reload the page and try again.", 400)
    question = body.get("question")
    question = question.strip() if isinstance(question, str) else ""
    if not question:
        return error("Please type a question first.", 400)
    if len(question) > 1000:
        return error("Your question is too long (1000 characters maximum).", 400)
    response = _forward(request, "POST", "/v1/ask", {"question": question})
    if response.status_code == 200:
        data = json.loads(response.content)
        data["answer"] = services.english_answer(data.get("answer", ""))
        data.setdefault("sources", [])
        return JsonResponse(data)
    return response


@kb_api(*UPLOADERS)
@require_http_methods(["POST"])
def quiz(request):
    """Generate multiple-choice questions from the knowledge base."""
    body = _json_body(request)
    if body is None:
        return error("The request was not valid. Please reload the page and try again.", 400)
    topic = body.get("topic")
    topic = topic.strip() if isinstance(topic, str) else ""
    if not topic:
        return error("Please type a topic first.", 400)
    if len(topic) > 300:
        return error("The topic is too long (300 characters maximum).", 400)
    try:
        count = int(body.get("count", 5))
    except (TypeError, ValueError):
        return error("The number of questions must be a whole number from 1 to 20.", 400)
    if not 1 <= count <= 20:
        return error("The number of questions must be a whole number from 1 to 20.", 400)
    difficulty = body.get("difficulty", "medium")
    if difficulty not in DIFFICULTIES:
        return error("Please choose Easy, Medium or Hard.", 400)
    return _forward(request, "POST", "/v1/quiz", {"topic": topic, "count": count, "difficulty": difficulty})


@kb_api(*UPLOADERS)
@require_http_methods(["GET", "POST"])
def documents(request):
    """GET: list the documents. POST: upload one (pdf, txt or md)."""
    if request.method == "GET":
        return _forward(request, "GET", "/v1/documents")
    upload = request.FILES.get("file")
    if upload is None:
        return error("Please choose a file to upload.", 400)
    if not upload.name.lower().endswith(ALLOWED_EXTENSIONS):
        return error("Only PDF, TXT and Markdown (.md) files can be uploaded.", 400)
    if upload.size > MAX_UPLOAD_BYTES:
        return error("That file is too large (20 MB maximum).", 413)
    title = request.POST.get("title", "").strip()[:120]
    tags = request.POST.get("tags", "").strip()[:120]
    response = _forward(
        request,
        "POST",
        "/v1/documents",
        files={"file": (upload.name, upload.read(), upload.content_type or "application/octet-stream")},
        data={"title": title, "tags": tags},
    )
    if response.status_code == 200:
        AuditService.log(request.user, "kb_document_uploaded", title or upload.name)
    return response


@kb_api(*DELETERS)
@require_http_methods(["DELETE"])
def document_delete(request, doc_id):
    """Remove one document from the shared knowledge base (school admins and super admins only)."""
    if not DOC_ID_RE.match(doc_id):
        return error("That document id is not valid.", 400)
    response = _forward(request, "DELETE", f"/v1/documents/{doc_id}")
    if response.status_code == 200:
        AuditService.log(request.user, "kb_document_deleted", doc_id)
    return response


@kb_api(*SUPER_ONLY)
@require_http_methods(["GET", "PUT"])
def model_settings(request):
    """Super Admin: read or change the AI model settings of the RAG service."""
    if request.method == "GET":
        return _forward(request, "GET", "/v1/admin/model")
    body = _json_body(request)
    if body is None:
        return error("The request was not valid. Please reload the page and try again.", 400)
    changes = {}
    for name, kind in MODEL_FIELDS.items():
        value = body.get(name)
        if value in (None, ""):
            continue  # empty = keep the current value (an empty API key keeps the old key)
        try:
            changes[name] = kind(value.strip() if isinstance(value, str) else value)
        except (TypeError, ValueError):
            return error(f"The value for {name.replace('_', ' ')} is not valid.", 400)
    response = _forward(request, "PUT", "/v1/admin/model", changes)
    if response.status_code == 200:
        AuditService.log(request.user, "kb_model_settings_changed", ", ".join(sorted(changes)) or "no changes")
    return response


@kb_api(*SUPER_ONLY)
@require_http_methods(["POST"])
def model_test(request):
    """Super Admin: check that the AI model answers."""
    return _forward(request, "POST", "/v1/admin/model/test")

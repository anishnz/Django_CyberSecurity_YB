"""Drop this file into a NEW Django app (e.g. `kb`) as kb/api.py.

It only forwards requests to the RAG service. Roles are decided HERE from the
logged-in user, and the RAG service enforces them again.

settings.py additions:
    RAG_BASE_URL    = os.getenv("RAG_BASE_URL", "http://127.0.0.1:9000")
    RAG_SERVICE_KEY = os.getenv("RAG_SERVICE_KEY")

kb/urls.py:
    from django.urls import path
    from . import api
    urlpatterns = api.urlpatterns

project urls.py (the one line you add):
    path("api/kb/", include("kb.urls")),
"""
import json

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.http import require_http_methods

TEACHER_UP = {"teacher", "super_admin"}


def role_of(user) -> str:
    """ADAPT THIS to how CyberQuest marks teachers (group, flag, profile field...)."""
    if user.is_superuser:
        return "super_admin"
    if user.groups.filter(name="Teacher").exists():
        return "teacher"
    return "student"


def _forward(request, method, rag_path, allowed=None, json_body=None, **kw):
    role = role_of(request.user)
    if allowed and role not in allowed:
        return JsonResponse({"detail": "Forbidden"}, status=403)
    try:
        r = requests.request(
            method,
            f"{settings.RAG_BASE_URL}{rag_path}",
            headers={"X-Service-Key": settings.RAG_SERVICE_KEY, "X-User-Role": role},
            json=json_body,
            timeout=180,
            **kw,
        )
        data = r.json()
    except (requests.RequestException, ValueError):
        return JsonResponse({"detail": "Knowledge base service unavailable"}, status=503)
    return JsonResponse(data, status=r.status_code, safe=False)


def _body(request) -> dict:
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


@login_required
@require_http_methods(["POST"])
def ask(request):
    return _forward(request, "POST", "/v1/ask", json_body=_body(request))


@login_required
@require_http_methods(["POST"])
def lesson_plan(request):
    return _forward(request, "POST", "/v1/lesson-plan", TEACHER_UP, _body(request))


@login_required
@require_http_methods(["POST"])
def quiz(request):
    return _forward(request, "POST", "/v1/quiz", TEACHER_UP, _body(request))


@login_required
@require_http_methods(["GET", "POST"])
def documents(request):
    if request.method == "GET":
        return _forward(request, "GET", "/v1/documents", TEACHER_UP)
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"detail": "file is required"}, status=400)
    return _forward(
        request, "POST", "/v1/documents", TEACHER_UP,
        files={"file": (f.name, f.read(), f.content_type)},
        data={"title": request.POST.get("title", ""), "tags": request.POST.get("tags", "")},
    )


@login_required
@require_http_methods(["DELETE"])
def document_delete(request, doc_id):
    return _forward(request, "DELETE", f"/v1/documents/{doc_id}", TEACHER_UP)


@login_required
@require_http_methods(["GET"])
def model_info(request):
    return _forward(request, "GET", "/v1/model-info")


@login_required
@require_http_methods(["GET", "PUT"])
def admin_model(request):
    # Only the Django Super Admin ever reaches the RAG admin endpoints.
    if request.method == "GET":
        return _forward(request, "GET", "/v1/admin/model", {"super_admin"})
    return _forward(request, "PUT", "/v1/admin/model", {"super_admin"}, _body(request))


@login_required
@require_http_methods(["POST"])
def admin_model_test(request):
    return _forward(request, "POST", "/v1/admin/model/test", {"super_admin"})


urlpatterns = [
    path("ask/", ask),
    path("lesson-plan/", lesson_plan),
    path("quiz/", quiz),
    path("documents/", documents),
    path("documents/<str:doc_id>/", document_delete),
    path("model-info/", model_info),
    path("admin/model/", admin_model),
    path("admin/model/test/", admin_model_test),
]

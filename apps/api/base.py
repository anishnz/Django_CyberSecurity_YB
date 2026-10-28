"""
base.py - The parent class for every JSON API endpoint (Template Method pattern)
================================================================================

Owner: Jihe Qi (task J-15)

A React app (or any other front end) talks to CyberQuest through small JSON
endpoints under ``/api/v1/``. Every endpoint is a child of ``ApiView``.

Concepts:
    * Abstraction: ``ApiView`` is abstract. A child class must write ``get_data()``
      (and ``post_data()`` if it accepts POST).
    * Template Method: ``ApiView.run()`` is the fixed recipe – check access, time the
      call, call the child's method, wrap the answer, add CORS headers. Children only
      fill in the one step that is different.
    * Inheritance: ``SuperAdminApiView`` changes one class attribute and so every
      endpoint under it is protected.
    * Encapsulation: the JSON "envelope" is built in one place, so every answer looks
      the same to React::

          {"ok": true,  "data": ..., "ms": 12}
          {"ok": false, "error": "friendly message", "ms": 3}

CORS (letting a React dev server on another port call the API):
    Only *public, read-only* endpoints send ``Access-Control-Allow-Origin``, and only
    for origins listed in the ``API_CORS_ORIGINS`` setting (for example
    ``http://localhost:5173``). Super Admin endpoints never allow other origins, so a
    stranger's web page cannot use a logged-in admin's session.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from time import perf_counter

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View

from apps.core.exceptions import CyberQuestError


class ApiView(View, ABC):
    """Abstract JSON endpoint. Children write ``get_data`` and/or ``post_data``."""

    name = ""  # short name shown on the API check page
    description = ""  # one line: what the endpoint returns
    super_admin_only = False
    allow_cors = True  # public read-only endpoints may be called from a React dev server
    http_method_names = ["get", "options"]

    # ------------------------------------------------------------------ steps for children
    @abstractmethod
    def get_data(self, request, **kwargs):
        """Return plain Python data (dict / list) that can be turned into JSON."""

    def post_data(self, request, **kwargs):  # pylint: disable=unused-argument
        """Optional: children that accept POST override this."""
        raise CyberQuestError("This endpoint does not accept POST.")

    # ------------------------------------------------------------------ the fixed recipe
    def get(self, request, **kwargs):
        return self.run(request, self.get_data, **kwargs)

    def post(self, request, **kwargs):
        return self.run(request, self.post_data, **kwargs)

    def options(self, request, *args, **kwargs):
        """CORS 'preflight' request from the browser: answer with headers only."""
        return self._cors(request, HttpResponse(status=204))

    def run(self, request, step, **kwargs) -> JsonResponse:
        """Template method: access check -> timed call -> JSON envelope -> CORS headers."""
        start = perf_counter()
        denied = self.check_access(request)
        if denied:
            return self._cors(request, self._envelope(False, start, error=denied[1], status=denied[0]))
        try:
            data = step(request, **kwargs)
        except CyberQuestError as exc:
            return self._cors(request, self._envelope(False, start, error=exc.message, status=exc.status))
        return self._cors(request, self._envelope(True, start, data=data))

    def check_access(self, request) -> tuple[int, str] | None:
        """Return (status, message) when the caller may not use this endpoint, otherwise None."""
        if not self.super_admin_only:
            return None
        user = request.user
        if not user.is_authenticated:
            return 401, "Please log in as the Super Admin."
        if getattr(user, "role", "") != "super_admin":
            return 403, "Only the Super Admin can use this endpoint."
        return None

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _envelope(ok: bool, start: float, *, data=None, error: str = "", status: int = 200) -> JsonResponse:
        body = {"ok": ok, "ms": round((perf_counter() - start) * 1000)}
        if ok:
            body["data"] = data
        else:
            body["error"] = error
        return JsonResponse(body, status=status, json_dumps_params={"ensure_ascii": False})

    def _cors(self, request, response):
        origin = request.headers.get("Origin", "")
        if self.allow_cors and origin and origin in getattr(settings, "API_CORS_ORIGINS", []):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type"
            response["Vary"] = "Origin"
        return response


class SuperAdminApiView(ApiView):  # pylint: disable=abstract-method
    """Endpoints for the Super Admin only. Same-origin only (no CORS). Still abstract on purpose."""

    super_admin_only = True
    allow_cors = False

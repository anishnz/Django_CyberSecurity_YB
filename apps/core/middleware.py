"""
middleware.py - Maintenance mode, friendly errors and security headers
======================================================================

Owners: Anish Shrestha (FriendlyErrorMiddleware, SecurityHeadersMiddleware);
        Rajneesh Kumar (MaintenanceModeMiddleware)

Concepts:
    * Middleware = code that runs for EVERY request, like a security guard at a door.
    * FriendlyErrorMiddleware turns CyberQuestError into a friendly page or a
      message + redirect, so users never see a Python traceback (NFR-02).
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .exceptions import CyberQuestError
from .models import SystemSettings

logger = logging.getLogger("cyberquest")

# Pages that still work while maintenance mode is on.
MAINTENANCE_ALLOWED = ("/accounts/login", "/health", "/static", "/media", "/admin")


class MaintenanceModeMiddleware:
    """Show a 'Back soon' page to everyone except Super Admins when maintenance mode is on."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(MAINTENANCE_ALLOWED):
            return self.get_response(request)
        try:
            cfg = SystemSettings.load()
        except Exception:  # pylint: disable=broad-except  # database not migrated yet
            return self.get_response(request)
        user = getattr(request, "user", None)
        is_super = bool(user and user.is_authenticated and getattr(user, "is_super_admin", False))
        if cfg.maintenance_mode and not is_super:
            return render(request, "core/maintenance.html", {"message": cfg.maintenance_message}, status=503)
        return self.get_response(request)


class FriendlyErrorMiddleware:
    """Catch CyberQuest errors and show them kindly."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        """Called by Django when a view raises an error."""
        if not isinstance(exception, CyberQuestError):
            return None  # Django's normal 500 handler (templates/500.html) deals with real bugs
        logger.warning("%s at %s: %s", type(exception).__name__, request.path, exception.message)
        if exception.status in (403, 404) or request.method == "GET":
            return render(request, "core/error.html",
                          {"status": exception.status, "message": exception.message,
                           "title": _title_for(exception)}, status=exception.status)
        messages.error(request, exception.message)
        back = request.META.get("HTTP_REFERER", "")
        if back and url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}):
            return redirect(back)
        return redirect("accounts:home")


def _title_for(exception: CyberQuestError) -> str:
    """Page heading for an error page."""
    name = type(exception).__name__
    return {"LevelLockedError": "Level locked", "NotFoundError": "Not found",
            "LicenseExpiredError": "Licence ended", "ReadOnlyError": "Read-only"}.get(
        name, "No access" if exception.status == 403 else "Please check and try again")


class SecurityHeadersMiddleware:
    """Extra browser security headers (Content Security Policy etc.)."""

    CSP = ("default-src 'self'; img-src 'self' data: https://i.ytimg.com https://maps.gstatic.com "
           "https://maps.googleapis.com; media-src 'self'; style-src 'self' 'unsafe-inline'; "
           "script-src 'self'; font-src 'self'; "
           "frame-src https://www.youtube-nocookie.com https://www.google.com; "
           "connect-src 'self'; frame-ancestors 'none'; form-action 'self'")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", self.CSP)
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

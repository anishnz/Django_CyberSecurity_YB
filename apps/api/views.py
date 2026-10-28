"""
views.py - API check page (Super Admin)
=======================================

Owner: Jihe Qi (task J-16)

One page with a test case per row and a "Check" button on each row:

* Website API for React – calls each public JSON endpoint and shows the status
  code, time and number of items.
* AI models and services – runs each provider's real connection test
  (Claude, OpenAI, Gemini, offline helper, Gmail, Google Maps, WhatsApp, Viber, share links).

The buttons are handled by static/js/api_check.js (no inline JavaScript, so the
Content Security Policy stays strict).
"""

from __future__ import annotations

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse

from apps.accounts.decorators import super_admin_required
from apps.integrations.adapters import ADAPTERS

from .endpoints import PUBLIC_ENDPOINTS


@super_admin_required
def api_check(request):
    """Show every test case with its own Check button."""
    public = [
        {"key": url_name.split(":")[1], "name": cls.name, "about": cls.description, "url": reverse(url_name)}
        for url_name, cls in PUBLIC_ENDPOINTS
    ]
    services = [
        {
            "key": name,
            "name": cls.label,
            "kind": cls.kind,
            "needs_key": cls.needs_secret,
            "url": reverse("api:integration_test", args=[name]),
        }
        for name, cls in ADAPTERS.items()
    ]
    return render(
        request,
        "api/check.html",
        {
            "public": public,
            "services": services,
            "base_url": request.build_absolute_uri("/api/v1/"),
            "cors": settings.API_CORS_ORIGINS,
        },
    )

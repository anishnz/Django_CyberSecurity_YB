"""
endpoints.py - JSON endpoints for a React front end (version 1)
===============================================================

Owner: Jihe Qi (task J-15)

Each class is a child of ``ApiView`` and only writes ``get_data`` (or ``post_data``).
That is polymorphism: the base class calls ``step(request)`` without knowing
which endpoint it is talking to.

Public (read-only, CORS allowed for API_CORS_ORIGINS):
    GET  /api/v1/                       list of endpoints
    GET  /api/v1/health/                is the server and database working?
    GET  /api/v1/levels/                the six learning levels
    GET  /api/v1/plans/                 plans, Level Pack prices, community discount
    GET  /api/v1/team/                  team members with photo links
    GET  /api/v1/meeting-photos/        meeting photos for the slider

Super Admin only (same site only, never CORS):
    GET  /api/v1/integrations/                  status of every AI model and service
    POST /api/v1/integrations/<provider>/test/  test one connection now
"""

from __future__ import annotations

from django.conf import settings
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from apps.core.exceptions import NotFoundError
from apps.integrations.adapters import ADAPTERS
from apps.integrations.models import IntegrationSetting
from apps.integrations.services import IntegrationService
from apps.licensing.plans import LEVEL_PACK_PRICES, PLAN_CLASSES

from .base import ApiView, SuperAdminApiView

GST = 0.15


class IndexApi(ApiView):
    """List every endpoint, so a React developer can see what exists."""

    name, description = "API index", "List of all endpoints"

    def get_data(self, request, **kwargs):
        return {
            "name": f"{settings.PROJECT['name']} API",
            "version": "v1",
            "endpoints": [
                {"name": cls.name, "url": request.build_absolute_uri(reverse(url_name)), "about": cls.description}
                for url_name, cls in PUBLIC_ENDPOINTS
            ],
        }


class HealthApi(ApiView):
    """Server and database check (React can call this first)."""

    name, description = "Health", "Server and database are working"

    def get_data(self, request, **kwargs):
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            db_ok = cur.fetchone()[0] == 1
        return {
            "status": "ok" if db_ok else "error",
            "database": connection.vendor,
            "version": settings.PROJECT["version"],
            "server_time": timezone.localtime().isoformat(timespec="seconds"),
        }


class LevelsApi(ApiView):
    """The six learning levels."""

    name, description = "Levels", "The six learning levels"

    def get_data(self, request, **kwargs):
        from apps.learning.models import Level  # pylint: disable=import-outside-toplevel

        return [
            {
                "number": lvl.number,
                "name": lvl.name,
                "audience": lvl.audience,
                "is_free": lvl.is_free,
                "topics": lvl.topics.count(),
            }
            for lvl in Level.objects.prefetch_related("topics")
        ]


class PlansApi(ApiView):
    """Plans and prices. Each Plan object answers for itself (polymorphism)."""

    name, description = "Plans and prices", "Plans, Level Packs and the community discount"

    def get_data(self, request, **kwargs):
        plans = []
        for cls in PLAN_CLASSES.values():
            normal, community = cls(None, None), cls(None, None, community_discount=True)
            plans.append(
                {
                    "code": cls.CODE,
                    "name": cls.DISPLAY_NAME,
                    "sections": normal.section_limit_label,
                    "monthly_nzd": float(normal.monthly_price()),
                    "monthly_community_nzd": float(community.monthly_price()),
                    "yearly_incl_gst_nzd": round(float(normal.monthly_price()) * 12 * (1 + GST), 2),
                }
            )
        return {
            "currency": "NZD",
            "gst": GST,
            "plans": plans,
            "level_packs": {f"level_{k}": float(v) for k, v in LEVEL_PACK_PRICES.items()},
        }


class TeamApi(ApiView):
    """Team members with photo links (photos are uploaded on the Website content page)."""

    name, description = "Team", "Team members with photo links"

    def get_data(self, request, **kwargs):
        from apps.website.services import WebsiteContentService  # pylint: disable=import-outside-toplevel

        return [
            {
                "name": m.name,
                "role": m.role,
                "bio": m.bio,
                "photo": request.build_absolute_uri(m.image_url) if m.image_url else None,
            }
            for m in WebsiteContentService.team()
        ]


class MeetingPhotosApi(ApiView):
    """Meeting photos for a React slider."""

    name, description = "Meeting photos", "Photos for the meetings slider"

    def get_data(self, request, **kwargs):
        from apps.website.services import WebsiteContentService  # pylint: disable=import-outside-toplevel

        return [
            {
                "title": p.title,
                "caption": p.caption,
                "place": p.place,
                "taken_on": p.taken_on.isoformat() if p.taken_on else None,
                "image": request.build_absolute_uri(p.image_url),
            }
            for p in WebsiteContentService.meeting_photos()
        ]


# ----------------------------------------------------------------------------- Super Admin only
class IntegrationStatusApi(SuperAdminApiView):
    """Saved status of every AI model and outside service. Keys are never sent."""

    name, description = "Integrations status", "AI models and services (Super Admin)"

    def get_data(self, request, **kwargs):
        rows = []
        for card in IntegrationService().cards():
            row, cls = card["row"], card["cls"]
            model = dict((k, v) for k, _, v in card["extra"]).get("model", "")
            rows.append(
                {
                    "provider": cls.provider,
                    "label": cls.label,
                    "kind": cls.kind,
                    "model": model,
                    "needs_key": cls.needs_secret,
                    "key_saved": bool(row and row.has_secret),
                    "enabled": bool(row and row.enabled) or not cls.needs_secret,
                    "status": row.status if row else ("ready" if not cls.needs_secret else "not_set"),
                    "last_checked": row.last_checked.isoformat() if row and row.last_checked else None,
                }
            )
        return rows


class IntegrationTestApi(SuperAdminApiView):
    """Test one connection now (POST, needs the CSRF token)."""

    name, description = "Test a connection", "Runs the provider's connection test (Super Admin)"
    http_method_names = ["post"]

    def get_data(self, request, **kwargs):  # GET is not allowed (http_method_names), kept for the ABC
        raise NotFoundError()

    def post_data(self, request, **kwargs):
        provider = kwargs["provider"]
        if provider not in ADAPTERS:
            raise NotFoundError(f"There is no provider called '{provider}'.")
        cls = ADAPTERS[provider]
        if not cls.needs_secret:  # offline helper and share links have no key and no settings row
            ok, message = cls().test_connection()
        elif not IntegrationSetting.objects.filter(provider=provider).exclude(_secret="").exists():
            ok, message = False, "No key saved yet. Add it on the Integrations page, then check again."
        else:
            ok, message = IntegrationService().test(provider)
        return {"provider": provider, "label": cls.label, "connected": ok, "message": message}


# (URL name, class) for the index and the API check page.
PUBLIC_ENDPOINTS = [
    ("api:index", IndexApi),
    ("api:health", HealthApi),
    ("api:levels", LevelsApi),
    ("api:plans", PlansApi),
    ("api:team", TeamApi),
    ("api:meeting_photos", MeetingPhotosApi),
]

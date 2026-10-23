"""
urls.py - Root URL map
======================

Owner: Anish Shrestha. Each app has its own urls.py; this file joins them.
"""
from importlib.util import find_spec

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import health_json

# (URL prefix, app) – an app's URLs are added once its urls.py exists.
APP_URLS = [
    ("", "website"), ("accounts/", "accounts"), ("admin-panel/", "core"), ("security/", "security"),
    ("schools/", "schools"), ("licences/", "licensing"), ("payments/", "payments"), ("learn/", "learning"),
    ("quiz/", "quizzes"), ("notifications/", "notifications"), ("email/", "emails"), ("tickets/", "helpdesk"),
    ("reports/", "reports"), ("help/", "helpcentre"), ("certificates/", "certificates"),
    ("announcements/", "announcements"), ("integrations/", "integrations"), ("ai/", "ai_assistant"),
    ("media-library/", "medialib"),
]

urlpatterns = [
    path("health/", health_json, name="health"),
    path("django-admin/", admin.site.urls),
]
urlpatterns += [path(prefix, include(f"apps.{app}.urls")) for prefix, app in APP_URLS
                if find_spec(f"apps.{app}.urls") is not None]

if settings.DEBUG or settings.DEMO_MODE:
    # Uploaded files are served by Django in this offline/school setup (waitress has no static file server).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.errors.not_found"
handler500 = "apps.core.errors.server_error"

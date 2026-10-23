"""urls.py - /admin-panel/ URLs for the Super Admin."""
from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.super_dashboard, name="super_dashboard"),
    path("settings/", views.settings_page, name="settings"),
    path("settings/<str:key>/", views.settings_review, name="settings_review"),
    path("system/", views.system, name="system"),
    path("system/backup/", views.backup_create, name="backup_create"),
    path("system/restore/", views.backup_restore, name="backup_restore"),
    path("system/reset-demo/", views.reset_demo, name="reset_demo"),
    path("system/switch/<slug:key>/", views.switch_toggle, name="switch_toggle"),
    path("audit/", views.audit_log, name="audit_log"),
]

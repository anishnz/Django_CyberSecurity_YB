"""urls.py - /integrations/ URLs (Super Admin)."""

from django.urls import path

from . import views

app_name = "integrations"
urlpatterns = [
    path("", views.integration_list, name="list"),
    path("ai-test/", views.ai_test, name="ai_test"),
    path("<slug:provider>/save/", views.integration_save, name="save"),
    path("<slug:provider>/test/", views.integration_test, name="test"),
    path("<slug:provider>/clear/", views.integration_clear, name="clear"),
]

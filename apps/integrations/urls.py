"""urls.py - /integrations/ URLs (Super Admin)."""

from django.urls import path

from . import views

app_name = "integrations"
urlpatterns = [
    path("", views.integration_list, name="list"),
    path("ai-test/", views.ai_test, name="ai_test"),
    path("ai-models/", views.ai_models, name="ai_models"),
    path("ai-models/check-all/", views.ai_check_all, name="ai_check_all"),
    path("whatsapp/send-test/", views.whatsapp_test, name="whatsapp_test"),
    path("<slug:provider>/save/", views.integration_save, name="save"),
    path("<slug:provider>/test/", views.integration_test, name="test"),
    path("<slug:provider>/clear/", views.integration_clear, name="clear"),
]

"""urls.py - /ai/ URLs."""

from django.urls import path

from . import views

app_name = "ai_assistant"
urlpatterns = [
    path("drafts/", views.draft_list, name="draft_list"),
    path("drafts/new/", views.draft_new, name="draft_new"),
    path("drafts/<int:pk>/", views.draft_detail, name="draft_detail"),
    path("drafts/<int:pk>/action/", views.draft_action, name="draft_action"),
    path("explain/", views.explain, name="explain"),
]

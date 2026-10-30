"""urls.py - /kb/ pages and /kb/api/ JSON endpoints."""

from django.urls import path

from . import api, views

app_name = "kb"
urlpatterns = [
    path("", views.ask, name="ask"),
    path("manage/", views.manage, name="manage"),
    path("api/ask/", api.ask, name="api_ask"),
    path("api/quiz/", api.quiz, name="api_quiz"),
    path("api/documents/", api.documents, name="api_documents"),
    path("api/documents/<str:doc_id>/", api.document_delete, name="api_document_delete"),
    path("api/admin/model/", api.model_settings, name="api_model"),
    path("api/admin/model/test/", api.model_test, name="api_model_test"),
]

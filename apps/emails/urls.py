"""urls.py - /emails/ URLs."""

from django.urls import path

from . import views

app_name = "emails"
urlpatterns = [
    path("templates/", views.template_list, name="template_list"),
    path("templates/<int:pk>/", views.template_edit, name="template_edit"),
    path("bulk/", views.bulk_email, name="bulk"),
    path("log/", views.email_log, name="log"),
    path("unsubscribe/<str:token>/", views.unsubscribe, name="unsubscribe"),
]

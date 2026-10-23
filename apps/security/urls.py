"""urls.py - /security/ URLs."""
from django.urls import path

from . import views

app_name = "security"
urlpatterns = [
    path("", views.security_log, name="log"),
    path("export.csv", views.security_log_csv, name="log_csv"),
]

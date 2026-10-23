"""urls.py - /notifications/ URLs."""
from django.urls import path

from . import views

app_name = "notifications"
urlpatterns = [
    path("", views.notification_list, name="list"),
    path("read/", views.mark_all_read, name="read_all"),
]

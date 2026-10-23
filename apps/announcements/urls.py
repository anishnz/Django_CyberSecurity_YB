"""urls.py - /announcements/ URLs."""
from django.urls import path

from . import views

app_name = "announcements"
urlpatterns = [
    path("", views.announcement_list, name="list"),
    path("new/", views.announcement_edit, name="new"),
    path("<int:pk>/", views.announcement_edit, name="edit"),
    path("<int:pk>/delete/", views.announcement_delete, name="delete"),
]

"""urls.py - /media-library/ URLs."""

from django.urls import path

from . import views

app_name = "medialib"
urlpatterns = [
    path("", views.media_list, name="media_list"),
    path("upload/", views.media_upload, name="media_upload"),
    path("video/", views.video_add, name="video_add"),
    path("<int:pk>/cultural-check/", views.cultural_approve, name="cultural_approve"),
    path("<int:pk>/delete/", views.media_delete, name="media_delete"),
    path("video/<int:pk>/delete/", views.video_delete, name="video_delete"),
]

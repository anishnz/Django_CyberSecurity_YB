"""urls.py - /help/ URLs."""

from django.urls import path

from . import views

app_name = "helpcentre"
urlpatterns = [
    path("", views.index, name="index"),
    path("<slug:slug>/", views.article, name="article"),
]

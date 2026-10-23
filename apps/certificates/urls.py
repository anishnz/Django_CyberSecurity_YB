"""urls.py - /certificates/ URLs."""

from django.urls import path

from . import views

app_name = "certificates"
urlpatterns = [
    path("", views.my_certificates, name="my_certificates"),
    path("<str:code>/download/", views.download, name="download"),
    path("verify/<str:code>/", views.verify, name="verify"),
    path("section/<int:pk>/zip/", views.section_zip, name="section_zip"),
]

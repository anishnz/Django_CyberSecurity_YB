"""urls.py - Public website URLs."""

from django.urls import path

from . import views

app_name = "website"
urlpatterns = [
    path("", views.home, name="home"),
    path("features/", views.features, name="features"),
    path("levels/", views.levels, name="levels"),
    path("pricing/", views.pricing, name="pricing"),
    path("community/", views.community, name="community"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("privacy/", views.privacy, name="privacy"),
    path("website/contact/", views.contact, name="contact"),
    path("guest/start/", views.guest_login, name="guest_login"),
    path("guest/", views.guest_tour, name="guest_tour"),
]

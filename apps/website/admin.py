"""admin.py - Django admin for slides and contact messages."""

from django.contrib import admin

from .models import ContactMessage, Slide

admin.site.register([Slide, ContactMessage])

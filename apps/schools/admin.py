"""admin.py - Django admin for schools."""

from django.contrib import admin

from .models import School, SchoolClass, Section, StudentProfile

admin.site.register([School, SchoolClass, Section, StudentProfile])

"""admin.py - Django admin for website content."""

from django.contrib import admin

from .models import ContactMessage, MeetingPhoto, Slide, TeamMember

admin.site.register([Slide, ContactMessage])


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Team members with photo, in display order."""

    list_display = ("name", "student_id", "role", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(MeetingPhoto)
class MeetingPhotoAdmin(admin.ModelAdmin):
    """Meeting photos for the slider."""

    list_display = ("title", "place", "taken_on", "order", "is_active")
    list_editable = ("order", "is_active")

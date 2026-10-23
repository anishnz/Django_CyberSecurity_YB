"""admin.py - Django admin registration for users. Owner: Anish Shrestha."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ImpersonationSession, User


@admin.register(User)
class CyberQuestUserAdmin(UserAdmin):
    """Django admin view of users with CyberQuest fields."""

    list_display = ("username", "first_name", "last_name", "role", "school", "is_active", "mfa_enabled")
    list_filter = ("role", "is_active", "mfa_enabled", "school")
    fieldsets = UserAdmin.fieldsets + (
        (
            "CyberQuest",
            {
                "fields": (
                    "role",
                    "school",
                    "phone",
                    "expires_at",
                    "is_temporary",
                    "mfa_enabled",
                    "locked_until",
                    "is_demo",
                )
            },
        ),
    )


admin.site.register(ImpersonationSession)

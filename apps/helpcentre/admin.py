"""admin.py - Help articles are edited in Django admin by the Super Admin. Owner: Dinesh Upreti."""

from django.contrib import admin

from .models import HelpArticle


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    """List, search and edit help articles."""

    list_display = ("title", "audience", "order", "is_published")
    search_fields = ("title", "summary", "body", "pages")

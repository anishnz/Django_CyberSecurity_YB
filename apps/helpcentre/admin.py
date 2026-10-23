from django.contrib import admin

from .models import HelpArticle


@admin.register(HelpArticle)
class HelpArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "order", "is_published")
    search_fields = ("title", "summary", "body", "pages")

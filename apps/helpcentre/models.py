"""
models.py - Help articles (Āwhina) and the page each one explains
=================================================================

Owner: Dinesh Upreti (task D-17). The Super Admin can edit articles in Django admin.
``pages`` lists the URL names (for example ``helpdesk:ticket_list``) where the
"Explain this page" button shows the article.
"""

from __future__ import annotations

from django.db import models

ALL_ROLES = "super_admin,school_admin,teacher,student,guest"


class HelpArticle(models.Model):
    """A help article and the pages it explains."""

    slug = models.SlugField(max_length=60, unique=True)
    title = models.CharField(max_length=120)
    audience = models.CharField(max_length=80, default=ALL_ROLES, help_text="Roles that can read it, comma separated.")
    pages = models.CharField(max_length=400, blank=True, help_text="URL names this article explains, comma separated.")
    summary = models.CharField(max_length=300)
    body = models.TextField(
        help_text="Short paragraphs. Lines starting with '- ' become bullet points; **bold** works."
    )
    video_url = models.URLField(blank=True, help_text="Optional YouTube link (how-to video).")
    order = models.PositiveSmallIntegerField(default=50)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self) -> str:
        return self.title

    def for_role(self, role: str) -> bool:
        return role in [r.strip() for r in self.audience.split(",")]

    def page_list(self) -> list[str]:
        return [p.strip() for p in self.pages.split(",") if p.strip()]

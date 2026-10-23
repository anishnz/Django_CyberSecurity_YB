"""services.py - Find help for a role or a page. Owner: Dinesh Upreti."""

from __future__ import annotations

from django.db.models import Q

from .content import ARTICLES, TOURS
from .models import HelpArticle


class HelpService:
    """Find help for a role or a page."""

    @staticmethod
    def ensure_defaults() -> int:
        """Create the starting help articles that do not exist yet."""
        made = 0
        for slug, (title, audience, pages, summary, body, order) in ARTICLES.items():
            _, created = HelpArticle.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "audience": audience,
                    "pages": pages,
                    "summary": summary,
                    "body": body,
                    "order": order,
                },
            )
            made += created
        return made

    @staticmethod
    def for_role(role: str, query: str = ""):
        qs = HelpArticle.objects.filter(is_published=True, audience__contains=role)
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(summary__icontains=query) | Q(body__icontains=query))
        return qs

    @staticmethod
    def for_page(view_name: str, role: str) -> HelpArticle | None:
        """The article that explains this page for this role (or None)."""
        if not view_name:
            return None
        for article in HelpArticle.objects.filter(is_published=True, pages__contains=view_name):
            if view_name in article.page_list() and article.for_role(role):
                return article
        return None

    @staticmethod
    def tour(role: str) -> list[tuple[str, str, str]]:
        return TOURS.get(role, TOURS["guest"])

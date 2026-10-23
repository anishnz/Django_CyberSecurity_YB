"""views.py - Help centre: search, article, getting-started tour. Owner: Dinesh Upreti."""

from django.shortcuts import get_object_or_404, render

from apps.medialib.youtube import safe_embed_url

from .models import HelpArticle
from .services import HelpService


def _role(request):
    return request.user.role if request.user.is_authenticated else "guest"


def index(request):
    query = request.GET.get("q", "").strip()[:80]
    role = _role(request)
    return render(
        request,
        "helpcentre/index.html",
        {"articles": HelpService.for_role(role, query), "q": query, "tour": HelpService.tour(role)},
    )


def article(request, slug):
    item = get_object_or_404(HelpArticle, slug=slug, is_published=True)
    if not item.for_role(_role(request)):
        item = None
    return render(
        request,
        "helpcentre/article.html",
        {"a": item, "video": safe_embed_url(item.video_url) if item and item.video_url else ""},
    )

"""views.py - The two Knowledge Base pages (Ask, Manage). The data comes from apps.kb.api."""

from django.shortcuts import render

from apps.accounts.decorators import role_required

from .api import ALL_ROLES, DELETERS, SUPER_ONLY, UPLOADERS


@role_required(*ALL_ROLES)
def ask(request):
    """Ask a question. Everyone can; staff also see a link to the Manage page."""
    return render(request, "kb/ask.html", {"can_manage": request.user.role in UPLOADERS})


@role_required(*UPLOADERS)
def manage(request):
    """Upload, list, delete documents and generate quiz questions. Model settings: Super Admin only."""
    role = request.user.role
    return render(
        request,
        "kb/manage.html",
        {"can_delete": role in DELETERS, "can_configure": role in SUPER_ONLY},
    )

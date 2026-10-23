"""views.py - Announcement list and editor. Owner: Dinesh Upreti."""

from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.core.clock import today
from apps.core.exceptions import CyberQuestError
from apps.integrations.adapters import ShareLinks

from .forms import AnnouncementForm
from .models import Announcement
from .services import AnnouncementService


@role_required("super_admin", "school_admin", "teacher", "student")
def announcement_list(request):
    """Current announcements for this user, and the ones an admin can manage."""
    service = AnnouncementService()
    can_manage = request.user.role in ("super_admin", "school_admin")
    rows = service.manageable_by(request.user) if can_manage else service.visible_to(request.user)
    items = [
        {"a": a, "whatsapp": ShareLinks.whatsapp(f"{a.title}: {a.body[:300]}")}
        for a in rows.select_related("school")[:100]
    ]
    return render(request, "announcements/list.html", {"items": items, "can_manage": can_manage})


@role_required("super_admin", "school_admin")
def announcement_edit(request, pk=None):
    """Create or edit an announcement (admins only)."""
    obj = (
        get_object_or_404(AnnouncementService.manageable_by(request.user), pk=pk)
        if pk
        else Announcement(starts_on=today())
    )
    form = AnnouncementForm(request.POST or None, instance=obj, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            AnnouncementService().save(request.user, form.save(commit=False))
        except CyberQuestError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, "Announcement saved.")
            return redirect("announcements:list")
    return render(request, "announcements/form.html", {"form": form, "obj": obj})


@role_required("super_admin", "school_admin")
@require_POST
def announcement_delete(request, pk):
    get_object_or_404(AnnouncementService.manageable_by(request.user), pk=pk).delete()
    messages.info(request, "Announcement removed.")
    return redirect("announcements:list")

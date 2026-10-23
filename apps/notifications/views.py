"""views.py - Notices (Pānui) page and 'mark all as read'. Owner: Rajneesh Kumar."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """All of my notifications."""
    items = Notification.objects.filter(recipient=request.user)[:100]
    return render(request, "notifications/list.html", {"items": items})


@login_required
@require_POST
def mark_all_read(request):
    """Mark every notification as read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get("HTTP_REFERER") or "notifications:list")

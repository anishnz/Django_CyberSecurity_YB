"""views.py - Security log page with filter and CSV export. Owner: Anish Shrestha (task A-17)."""
import csv

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import super_admin_required

from .models import SecurityEvent


def _filtered(request):
    rows = SecurityEvent.objects.all()
    event, user = request.GET.get("event", ""), request.GET.get("user", "").strip()
    if event:
        rows = rows.filter(event=event)
    if user:
        rows = rows.filter(username__icontains=user)
    return rows, event, user


@super_admin_required
def security_log(request):
    """Security events: logins, failures, lockouts, Login as, MFA, uploads, API keys."""
    rows, event, user = _filtered(request)
    events = sorted(set(SecurityEvent.objects.order_by().values_list("event", flat=True)))
    return render(request, "security/log.html", {
        "page": Paginator(rows, 40).get_page(request.GET.get("page")), "event": event, "user": user, "events": events})


@super_admin_required
def security_log_csv(request):
    """Download the filtered security log as CSV."""
    rows, _, _ = _filtered(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="cyberquest_security_log.csv"'
    writer = csv.writer(response)
    writer.writerow(["time", "user", "event", "ip", "path", "details"])
    for r in rows[:5000]:
        writer.writerow([r.created_at.isoformat(timespec="seconds"), r.username, r.event, r.ip_address, r.path, r.details])
    return response

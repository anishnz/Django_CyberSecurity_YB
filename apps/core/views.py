"""
views.py - Super Admin dashboard, settings (overwrite warning), system, audit log, health
========================================================================================

Owners: Anish Shrestha (dashboard, settings); Rajneesh Kumar (system, audit, health)
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import super_admin_required

from . import health
from .backup import RESTORE_WORD, BackupService
from .exceptions import ConfirmationRequiredError
from .models import AuditLog, BackupRecord, FeatureSwitch
from .services import AuditService, SettingsService

User = get_user_model()
RESET_DEMO_WORD = "RESET DEMO"


def health_json(request):  # pylint: disable=unused-argument
    """/health/ – machine-readable health check (Docker HEALTHCHECK uses it)."""
    data = health.run_all()
    return JsonResponse(data, status=200 if data["status"] == "ok" else 503)


@super_admin_required
def super_dashboard(request):
    """Super Admin home: totals, licences ending soon, recent security events."""
    from apps.reports.services import BIService  # pylint: disable=import-outside-toplevel
    from apps.security.models import SecurityEvent  # pylint: disable=import-outside-toplevel

    bi = BIService()
    return render(
        request,
        "core/super_dashboard.html",
        {
            "kpis": bi.platform_kpis(),
            "expiring": bi.licences_ending(30),
            "security": SecurityEvent.objects.all()[:8],
            "audit": AuditLog.objects.all()[:8],
            "pending_payments": bi.pending_payments(),
            "open_tickets": bi.open_tickets(),
        },
    )


@super_admin_required
def settings_page(request):
    """List settings; 'Review' posts to settings_review (overwrite warning)."""
    return render(request, "core/settings.html", {"rows": SettingsService().rows()})


@super_admin_required
@require_POST
def settings_review(request, key):
    """Step 1 shows OLD → NEW and asks to confirm. Step 2 (confirmed=yes) saves."""
    service = SettingsService()
    value = request.POST.get("value", "")
    if request.POST.get("confirmed") != "yes":
        old, new = service.preview_change(key, value)
        return render(
            request,
            "core/confirm.html",
            {
                "title": "Change system setting",
                "warning": "You are about to overwrite a system setting. " "It affects every school.",
                "changes": [(key, old, new)],
                "hidden": {"value": value, "confirmed": "yes"},
                "cancel_url": "core:settings",
            },
        )
    old, new = service.apply_change(key, value, request.user)
    messages.success(request, f"Setting '{key}' changed from {old} to {new}.")
    return redirect("core:settings")


@super_admin_required
def system(request):
    """System page: status, backups, feature switches, reset demo."""
    return render(
        request,
        "core/system.html",
        {
            "health": health.run_all(),
            "backups": BackupRecord.objects.all()[:10],
            "switches": FeatureSwitch.objects.all(),
            "restore_word": RESTORE_WORD,
            "reset_word": RESET_DEMO_WORD,
        },
    )


@super_admin_required
@require_POST
def backup_create(request):
    record = BackupService().create(request.user, "manual")
    messages.success(request, f"Backup created: {record.file_name}")
    return redirect("core:system")


@super_admin_required
@require_POST
def backup_restore(request):
    safety = BackupService().restore(request.POST.get("name", ""), request.POST.get("confirm", ""), request.user)
    messages.success(request, f"Backup restored. A safety copy was saved first: {safety}")
    return redirect("core:system")


@super_admin_required
@require_POST
def reset_demo(request):
    """Reload demo data (needs the words RESET DEMO). A backup is made first."""
    if request.POST.get("confirm", "").strip() != RESET_DEMO_WORD:
        raise ConfirmationRequiredError(f"Please type {RESET_DEMO_WORD} to confirm.")
    try:
        backup = BackupService().create(request.user, "beforereset").file_name
    except Exception:  # pylint: disable=broad-except  # PostgreSQL: no in-app backup
        backup = "not made (PostgreSQL)"
    call_command("seed_demo", reset=True, verbosity=0)
    AuditService.log(request.user, "demo_reset", details=f"backup {backup}")
    messages.success(request, f"Demo data has been reset. Backup: {backup}. Please log in again if needed.")
    return redirect("core:system")


@super_admin_required
@require_POST
def switch_toggle(request, key):
    """Turn a feature switch on or off."""
    switch = FeatureSwitch.objects.get(key=key)
    switch.enabled = not switch.enabled
    switch.save(update_fields=["enabled"])
    AuditService.log(request.user, "feature_switch", key, not switch.enabled, switch.enabled)
    messages.success(request, f"{switch.label} is now {'on' if switch.enabled else 'off'}.")
    return redirect("core:system")


@super_admin_required
def audit_log(request):
    """Audit log with a filter by action."""
    rows = AuditLog.objects.all()
    action = request.GET.get("action", "")
    if action:
        rows = rows.filter(action=action)
    actions = AuditLog.objects.order_by().values_list("action", flat=True).distinct()
    return render(
        request,
        "core/audit_log.html",
        {
            "page": Paginator(rows, 40).get_page(request.GET.get("page")),
            "action": action,
            "actions": sorted(set(actions)),
        },
    )

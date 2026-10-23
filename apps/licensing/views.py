"""
views.py - Licences, product keys, Level Packs and discounts
============================================================

Owner: Rajneesh Kumar (task R-06). Students never reach these pages.
"""

from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required, super_admin_required
from apps.core.clock import today
from apps.core.exceptions import AccessDeniedError, ValidationError
from apps.core.services import AuditService
from apps.schools.models import School

from .keys import LicenseKeyValidator
from .models import License
from .plans import PLAN_CHOICES
from .services import LevelPackService, LicenseService


@super_admin_required
def licence_list(request):
    """Super Admin: every school's licence, plan, days left and discount."""
    rows = []
    for lic in License.objects.select_related("school").order_by("expiry_date"):
        plan = lic.plan_obj
        rows.append(
            {
                "lic": lic,
                "plan": plan,
                "status": plan.status_label(today()),
                "price": plan.monthly_price(),
                "packs": sorted(LevelPackService.owned_levels(lic.school) - {1}),
            }
        )
    return render(request, "licensing/licence_list.html", {"rows": rows})


@super_admin_required
def key_generator(request):
    """Company tool: make product keys and Level Pack keys."""
    generated, chosen = None, {}
    if request.method == "POST":
        chosen = request.POST
        school = get_object_or_404(School, code=request.POST.get("school_code"))
        kind = request.POST.get("kind", "")
        expiry_text = request.POST.get("expiry", "")
        try:
            expiry = date.fromisoformat(expiry_text) if expiry_text else None
        except ValueError as exc:
            raise ValidationError("Please choose a valid expiry date.") from exc
        if kind != "UNLIMITED" and expiry is None:
            raise ValidationError("Please choose an expiry date.")
        generated = LicenseKeyValidator().generate(school.code, kind, expiry)
        AuditService.log(request.user, "key_generated", school.code, new=kind)
    return render(
        request,
        "licensing/keys.html",
        {
            "schools": School.objects.order_by("name"),
            "generated": generated,
            "chosen": chosen,
            "plans": PLAN_CHOICES,
            "levels": [f"L{n}" for n in range(2, 7)],
        },
    )


def _school_for(request, school_id=None) -> School:
    user = request.user
    if user.is_super_admin and school_id:
        return get_object_or_404(School, pk=school_id)
    if user.is_school_admin and user.school:
        return user.school
    raise AccessDeniedError()


@role_required("super_admin", "school_admin")
@require_POST
def apply_key(request, school_id=None):
    """Apply a product key (School Admin for own school, Super Admin for any)."""
    school = _school_for(request, school_id)
    lic = LicenseService().apply_product_key(school, request.POST.get("key", ""), request.user)
    messages.success(request, f"Licence updated: {lic.get_plan_display()} until {lic.expiry_date:%d %b %Y}.")
    return redirect(request.META.get("HTTP_REFERER") or "licensing:my_licence")


@role_required("super_admin", "school_admin")
@require_POST
def apply_pack(request, school_id=None):
    """Apply a Level Pack key."""
    school = _school_for(request, school_id)
    pack = LevelPackService().apply_pack_key(school, request.POST.get("key", ""), request.user)
    messages.success(request, f"Level Pack {pack.level} added. Ka pai!")
    return redirect(request.META.get("HTTP_REFERER") or "licensing:my_licence")


@super_admin_required
@require_POST
def set_discount(request, school_id):
    """Super Admin: switch the community discount for a school."""
    school = get_object_or_404(School, pk=school_id)
    lic = LicenseService.set_discount(school, request.POST.get("on") == "1", request.user)
    messages.success(request, f"Community discount {'on' if lic.community_discount else 'off'} for {school.name}.")
    return redirect("licensing:licence_list")


@role_required("school_admin")
def my_licence(request):
    school = request.user.school
    lic = LicenseService.get(school)
    return render(
        request,
        "licensing/my_licence.html",
        {
            "school": school,
            "lic": lic,
            "plan": lic.plan_obj if lic else None,
            "status": lic.plan_obj.status_label(today()) if lic else "",
            "packs": LevelPackService().table(school),
        },
    )

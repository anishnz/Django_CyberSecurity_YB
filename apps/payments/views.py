"""
views.py - Pay by bank transfer (School Admin) and review payslips (Super Admin)
===============================================================================

Owners: Dinesh Upreti (screens), Rajneesh Kumar (rules in services.py)
"""

from __future__ import annotations

from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required, super_admin_required
from apps.core.exceptions import AccessDeniedError, CyberQuestError
from apps.core.models import SystemSettings
from apps.licensing.plans import LEVEL_PACK_PRICES, PLAN_CLASSES

from .forms import PaymentForm
from .models import Payment
from .services import PAID_PLANS, PaymentService


def _visible(user):
    qs = Payment.objects.select_related("school", "submitted_by")
    return qs if user.is_super_admin else qs.filter(school=user.school)


@role_required("school_admin")
def upload(request):
    """School Admin: see prices + bank details, then upload the payslip."""
    form = PaymentForm(request.POST or None, request.FILES or None)
    service = PaymentService()
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            payment = service.submit(
                request.user,
                purpose=d["purpose"],
                plan=d.get("plan") or "",
                months=d.get("months") or 0,
                level=d.get("level"),
                bank_reference=d["bank_reference"],
                paid_on=d["paid_on"],
                payslip=d["payslip"],
                request=request,
            )
        except CyberQuestError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, f"Thank you. Payment {payment.number} (${payment.total}) is waiting for review.")
            return redirect("payments:payment_list")
    school = request.user.school
    quotes = []
    for plan in PAID_PLANS:
        for months in (1, 12):
            quotes.append(service.quote(school, "plan", plan, months))
    for level in LEVEL_PACK_PRICES:
        try:
            quotes.append(service.quote(school, "pack", level=level))
        except CyberQuestError:
            pass
    return render(
        request,
        "payments/upload.html",
        {"form": form, "quotes": quotes, "cfg": SystemSettings.load(), "reference": f"CQ-{school.code}"},
    )


@role_required("super_admin", "school_admin")
def payment_list(request):
    """Payments waiting for review (Super Admin) or the school's own payments."""
    status = request.GET.get("status", "pending" if request.user.is_super_admin else "")
    rows = _visible(request.user)
    if status:
        rows = rows.filter(status=status)
    return render(
        request,
        "payments/list.html",
        {"rows": rows[:200], "status": status, "statuses": Payment.STATUSES, "plans": PLAN_CLASSES},
    )


@role_required("super_admin", "school_admin")
def payment_detail(request, pk):
    payment = get_object_or_404(_visible(request.user), pk=pk)
    return render(request, "payments/detail.html", {"p": payment})


@role_required("super_admin", "school_admin")
def payslip(request, pk):
    """Payslips are private: only the school and the Super Admin can open them."""
    payment = get_object_or_404(_visible(request.user), pk=pk)
    return FileResponse(payment.payslip.open("rb"), filename=f"{payment.number}{payment.payslip.name[-4:]}")


@super_admin_required
@require_POST
def review(request, pk):
    """Super Admin approves or rejects a payment."""
    payment = get_object_or_404(Payment, pk=pk)
    action, note = request.POST.get("action"), request.POST.get("note", "")
    service = PaymentService()
    if action == "approve":
        service.approve(payment, request.user, note)
        messages.success(request, f"{payment.number} approved. {payment.item} is now active for {payment.school}.")
    elif action == "reject":
        service.reject(payment, request.user, note)
        messages.info(request, f"{payment.number} rejected. The school was told why.")
    else:
        raise AccessDeniedError()
    return redirect("payments:payment_detail", pk=pk)


@role_required("super_admin", "school_admin")
def receipt(request, pk):
    payment = get_object_or_404(_visible(request.user), pk=pk)
    response = HttpResponse(PaymentService.receipt_pdf(payment), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="receipt_{payment.number}.pdf"'
    return response

"""
views.py - Email templates, bulk email (preview then send), email log, unsubscribe
==================================================================================

Owners: Rajneesh Kumar (logic), Dinesh Upreti (screens)
"""
from __future__ import annotations

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required, super_admin_required
from apps.core.services import AuditService

from .forms import BulkEmailForm, EmailTemplateForm
from .models import EmailLog, EmailTemplate, Unsubscribe
from .services import EmailService, render_text


@super_admin_required
def template_list(request):
    EmailService.ensure_defaults()
    return render(request, "emails/template_list.html", {"templates": EmailTemplate.objects.all()})


@super_admin_required
def template_edit(request, pk):
    tpl = get_object_or_404(EmailTemplate, pk=pk)
    form = EmailTemplateForm(request.POST or None, instance=tpl)
    if request.method == "POST" and form.is_valid():
        form.save()
        AuditService.log(request.user, "email_template_saved", tpl.key)
        messages.success(request, f"Template '{tpl.name}' saved.")
        return redirect("emails:template_list")
    sample = {"name": "Aroha", "school": "Everest Primary (demo)", "ticket": "CQ-0042", "title": "Cannot log in",
              "reply": "Please try again now.", "link": "https://example.org/reset", "student": "Nikau", "levels": 2,
              "message": "Cyber Smart Week starts on Monday.", "unsubscribe": "https://example.org/unsubscribe",
              "date": "30 Nov 2026", "status": "approved", "reference": "PAY-0007", "note": ""}
    return render(request, "emails/template_edit.html", {"form": form, "tpl": tpl,
                  "preview_subject": render_text(tpl.subject, sample), "preview_body": render_text(tpl.body, sample)})


@role_required("super_admin", "school_admin")
def bulk_email(request):
    """Step 1: choose template and audience. Step 2: preview count and sample. Step 3: send."""
    form = BulkEmailForm(request.POST or None, user=request.user)
    ctx = {"form": form}
    if request.method == "POST" and form.is_valid():
        tpl = form.cleaned_data["template"]
        school = form.cleaned_data.get("school") if request.user.is_super_admin else request.user.school
        service = EmailService()
        people = service.recipients(tpl.audience, school)
        extra = {"message": form.cleaned_data["message"], "school": school.name if school else "your school", "levels": "some"}
        if request.POST.get("confirmed") != "yes":
            sample = {**extra, **(people[0] if people else {"name": "(nobody)"}), "unsubscribe": "(link)"}
            ctx.update(preview=True, count=len(people), tpl=tpl, sample_subject=render_text(tpl.subject, sample),
                       sample_body=render_text(tpl.body, sample))
        else:
            batch, sent, failed = service.bulk_send(tpl, people, extra, request.build_absolute_uri("/")[:-1])
            AuditService.log(request.user, "bulk_email", tpl.key, new=f"batch {batch}: {sent} sent, {failed} failed")
            messages.success(request, f"Bulk email sent: {sent} sent, {failed} failed (batch {batch}).")
            return redirect("emails:bulk")
    return render(request, "emails/bulk.html", ctx)


@super_admin_required
def email_log(request):
    rows = EmailLog.objects.all()
    status = request.GET.get("status", "")
    if status:
        rows = rows.filter(status=status)
    return render(request, "emails/log.html", {"page": Paginator(rows, 40).get_page(request.GET.get("page")),
                                               "status": status, "statuses": EmailLog.STATUSES})


def unsubscribe(request, token):
    """Public link in bulk emails. GET asks, POST confirms (so link scanners do not unsubscribe people)."""
    row = get_object_or_404(Unsubscribe, token=token)
    if request.method == "POST":
        row.unsubscribed = request.POST.get("action") != "resubscribe"
        row.save()
    return render(request, "emails/unsubscribe.html", {"row": row})

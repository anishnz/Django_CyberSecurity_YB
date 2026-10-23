"""
views.py - AI drafts (list, new, detail with approvals) and "Explain this page"
===============================================================================

Owners: Anish Shrestha (logic, task A-20), Dinesh Upreti (screens)
"""

from __future__ import annotations

import time

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.core.exceptions import CyberQuestError

from .forms import DraftEditForm, DraftRequestForm
from .models import AIDraft
from .services import MAX_EXPLAINS_PER_HOUR, AIDraftService, PageHelper

STAFF = ("super_admin", "school_admin", "teacher")


@role_required(*STAFF)
def draft_list(request):
    """AI drafts of the school, with the ones waiting for this Cultural Guide."""
    status = request.GET.get("status", "")
    rows = AIDraftService.visible_to(request.user)
    if status:
        rows = rows.filter(status=status)
    waiting_cultural = AIDraftService.visible_to(request.user).filter(
        status=AIDraft.DRAFT, needs_cultural_check=True, cultural_approved_by__isnull=True
    )
    return render(
        request,
        "ai_assistant/list.html",
        {
            "rows": rows[:100],
            "status": status,
            "statuses": AIDraft.STATUSES,
            "waiting_cultural": waiting_cultural if request.user.is_cultural_guide else [],
        },
    )


@role_required(*STAFF)
def draft_new(request):
    """Ask the AI helper for a new draft."""
    form = DraftRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            draft = AIDraftService().create(
                request.user, form.cleaned_data["kind"], form.cleaned_data["request_text"], form.cleaned_data["topic"]
            )
        except CyberQuestError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, f"Draft made with {draft.provider}. Please check it before approving.")
            return redirect("ai_assistant:draft_detail", pk=draft.pk)
    return render(request, "ai_assistant/new.html", {"form": form})


@role_required(*STAFF)
def draft_detail(request, pk):
    """One draft: edit the text and see the approvals."""
    draft = get_object_or_404(AIDraftService.visible_to(request.user), pk=pk)
    form = DraftEditForm(
        request.POST or None, initial={"text": draft.text, "needs_cultural_check": draft.needs_cultural_check}
    )
    if request.method == "POST" and form.is_valid():
        try:
            AIDraftService.edit(
                request.user, draft, form.cleaned_data["text"], form.cleaned_data["needs_cultural_check"]
            )
        except CyberQuestError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, "Draft saved. It needs the approvals again.")
            return redirect("ai_assistant:draft_detail", pk=pk)
    return render(request, "ai_assistant/detail.html", {"d": draft, "form": form})


@role_required(*STAFF)
@require_POST
def draft_action(request, pk):
    """Approve (teacher / cultural), reject, or publish as a practice question."""
    draft = get_object_or_404(AIDraftService.visible_to(request.user), pk=pk)
    action = request.POST.get("action", "")
    if action in ("teacher", "cultural"):
        AIDraftService.approve(request.user, draft, action)
        messages.success(
            request, "Approval saved." + (" The draft is approved." if draft.status == AIDraft.APPROVED else "")
        )
    elif action == "reject":
        AIDraftService.reject(request.user, draft, request.POST.get("note", ""))
        messages.info(request, "Draft rejected.")
    elif action == "publish":
        question = AIDraftService().publish_question(request.user, draft)
        messages.success(request, f"Practice question Q{question.pk} added for your school.")
    return redirect("ai_assistant:draft_detail", pk=pk)


@require_POST
def explain(request):
    """Answer a question about the current page (also for guests). Limited to 20 per hour per browser."""
    stamps = [t for t in request.session.get("ai_explain", []) if t > time.time() - 3600]
    role = request.user.role if request.user.is_authenticated else "guest"
    if len(stamps) >= MAX_EXPLAINS_PER_HOUR:
        answer, article = (
            "You asked a lot of questions this hour. Please open the Help centre or try again later.",
            None,
        )
    else:
        answer, article = PageHelper.answer(request.POST.get("page", ""), role, request.POST.get("question", ""))
        request.session["ai_explain"] = stamps + [time.time()]
    return render(
        request,
        "ai_assistant/explain.html",
        {"answer": answer, "article": article, "question": request.POST.get("question", "")[:300]},
    )

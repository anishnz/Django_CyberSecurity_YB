"""
views.py - Ticket list, new ticket, ticket detail (reply, status, assign), report a question
===========================================================================================

Owners: Dinesh Upreti (screens, task D-14), Rajneesh Kumar (rules in services.py)
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.core.exceptions import CyberQuestError
from apps.learning.models import Question

from .forms import CommentForm, ReportQuestionForm, TicketForm
from .models import Ticket
from .services import TRANSITIONS, TicketService

User = get_user_model()
MEMBERS = ("super_admin", "school_admin", "teacher", "student")


@role_required(*MEMBERS)
def ticket_list(request):
    service = TicketService()
    rows = service.visible_to(request.user)
    status, q, mine = request.GET.get("status", "open"), request.GET.get("q", "").strip(), request.GET.get("mine")
    if status == "open":
        rows = rows.exclude(status__in=[Ticket.RESOLVED, Ticket.CLOSED])
    elif status:
        rows = rows.filter(status=status)
    if q:
        rows = rows.filter(Q(number__icontains=q) | Q(title__icontains=q) | Q(requester_name__icontains=q))
    if mine:
        rows = rows.filter(assignee=request.user)
    page = Paginator(rows, 25).get_page(request.GET.get("page"))
    for t in page:
        t.overdue = service.is_overdue(t)
    base = service.visible_to(request.user)
    counts = {s: base.filter(status=s).count() for s, _ in Ticket.STATUSES}
    return render(request, "helpdesk/ticket_list.html", {"page": page, "status": status, "q": q, "mine": mine,
                                                         "statuses": Ticket.STATUSES, "counts": counts})


@role_required(*MEMBERS)
def ticket_new(request):
    form = TicketForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            ticket = TicketService().create(requester=request.user, files=form.cleaned_data["files"], request=request,
                                            **{k: form.cleaned_data[k] for k in ("title", "description", "category", "priority")})
        except CyberQuestError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, f"Ticket {ticket.number} created. We will reply soon.")
            return redirect("helpdesk:ticket_detail", pk=ticket.pk)
    return render(request, "helpdesk/ticket_form.html", {"form": form})


def _staff_choices(ticket):
    qs = User.objects.filter(is_active=True, role="super_admin")
    if ticket.school_id:
        qs = qs | User.objects.filter(is_active=True, school_id=ticket.school_id, role__in=["school_admin", "teacher"])
    return qs.order_by("role", "first_name")


@role_required(*MEMBERS)
def ticket_detail(request, pk):
    service = TicketService()
    ticket = get_object_or_404(Ticket.objects.select_related("requester", "assignee", "school", "question"), pk=pk)
    service.check_view(request.user, ticket)
    manage = service.can_manage(request.user, ticket)
    form = CommentForm(request.POST or None, request.FILES or None)
    if not manage:
        form.fields.pop("internal")
    if request.method == "POST" and form.is_valid():
        try:
            service.comment(ticket, request.user, form.cleaned_data["body"], form.cleaned_data.get("internal", False),
                            form.cleaned_data["files"], request)
        except CyberQuestError as exc:
            form.add_error(None, exc.message)
        else:
            messages.success(request, "Reply added.")
            return redirect("helpdesk:ticket_detail", pk=ticket.pk)
    comments = ticket.comments.prefetch_related("attachments").select_related("author")
    if not manage:
        comments = comments.filter(is_internal=False)
    return render(request, "helpdesk/ticket_detail.html", {
        "t": ticket, "form": form, "comments": comments, "manage": manage, "overdue": service.is_overdue(ticket),
        "moves": [(s, label) for s, label in Ticket.STATUSES if s in TRANSITIONS.get(ticket.status, set())],
        "staff": _staff_choices(ticket) if manage else [], "history": ticket.history.select_related("user")[:20],
        "can_close": request.user.pk == ticket.requester_id and Ticket.CLOSED in TRANSITIONS.get(ticket.status, set())})


@role_required(*MEMBERS)
@require_POST
def ticket_move(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    TicketService().check_view(request.user, ticket)
    TicketService().move(ticket, request.POST.get("status", ""), request.user)
    messages.success(request, f"Ticket {ticket.number} is now {ticket.get_status_display()}.")
    return redirect("helpdesk:ticket_detail", pk=pk)


@role_required("super_admin", "school_admin", "teacher")
@require_POST
def ticket_assign(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    assignee = get_object_or_404(_staff_choices(ticket), pk=request.POST.get("assignee") or 0)
    TicketService().assign(ticket, assignee, request.user)
    messages.success(request, f"Assigned to {assignee}.")
    return redirect("helpdesk:ticket_detail", pk=pk)


@role_required(*MEMBERS)
def report_question(request, question_pk):
    """'Report this question' from a practice question → a content ticket."""
    question = get_object_or_404(Question, pk=question_pk)
    form = ReportQuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ticket = TicketService().report_question(request.user, question, form.cleaned_data["note"])
        messages.success(request, f"Thank you! Ticket {ticket.number} was sent to your teacher.")
        return redirect("helpdesk:ticket_detail", pk=ticket.pk)
    return render(request, "helpdesk/report_question.html", {"form": form, "question": question})

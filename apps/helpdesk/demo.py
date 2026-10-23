"""demo.py - A few demo tickets so the help desk and BI pages are not empty. Owner: Jihe Qi (test data)."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Ticket, TicketComment, TicketHistory
from .services import SLA

User = get_user_model()


def _ticket(
    title, desc, category, priority, requester, status, age_hours, *, assignee=None, reply="", email="", name=""
):
    created = timezone.now() - timedelta(hours=age_hours)
    t = Ticket.objects.create(
        title=title,
        description=desc,
        category=category,
        priority=priority,
        requester=requester,
        requester_email=email or getattr(requester, "email", ""),
        requester_name=name or (requester.get_full_name() if requester else ""),
        school=getattr(requester, "school", None),
        assignee=assignee,
        status=status,
        sla_due=created + SLA[priority],
    )
    Ticket.objects.filter(pk=t.pk).update(created_at=created)
    if reply and assignee:
        TicketComment.objects.create(ticket=t, author=assignee, author_name=str(assignee), body=reply)
    if status in (Ticket.RESOLVED, Ticket.CLOSED):
        Ticket.objects.filter(pk=t.pk).update(resolved_at=created + timedelta(hours=min(age_hours, 20)))
        TicketHistory.objects.create(ticket=t, user=assignee, field="status", old_value="open", new_value=status)
    return t


def load_demo_tickets(p: dict) -> int:
    """Six tickets across roles and statuses (website, student, teacher, school admin)."""
    Ticket.objects.filter(school__is_demo=True).delete()
    Ticket.objects.filter(requester_email__endswith="@demo.cyberquest.local", requester__isnull=True).delete()
    tama, bikash = p["s7a"]["Tama"], p["everest"]["Bikash"]
    sione, sita = p["sione"], p["sita"]
    super_admin = User.objects.filter(role="super_admin").first()
    school_admin = User.objects.filter(role="school_admin", school=sione.school).first()
    _ticket(
        "I forgot my password",
        "I cannot log in after the holidays. Can you reset it please?",
        "login",
        "normal",
        tama,
        Ticket.RESOLVED,
        50,
        assignee=sione,
        reply="Kia ora Tama, I reset it. Your new temporary password is with your teacher.",
    )
    _ticket(
        "Level 2 question looks wrong",
        "In the phishing topic two answers look right to me.",
        "content",
        "low",
        bikash,
        Ticket.IN_PROGRESS,
        30,
        assignee=sita,
        reply="Thanks Bikash, I am checking it with the content team.",
    )
    _ticket(
        "Projector shows the quiz too small",
        "Can the quiz text be bigger for the class screen?",
        "feature",
        "normal",
        sione,
        Ticket.ASSIGNED,
        10,
        assignee=school_admin,
    )
    _ticket(
        "Licence renewal for next year",
        "We would like to move from Basic to Standard next term.",
        "licence",
        "high",
        school_admin,
        Ticket.WAITING,
        40,
        assignee=super_admin,
        reply="Please upload the bank payslip on the Payments page.",
    )
    _ticket(
        "Website: question about pricing",
        "Do kura kaupapa Māori get the community discount?",
        "contact",
        "normal",
        None,
        Ticket.OPEN,
        3,
        email="principal@demo.cyberquest.local",
        name="Demo visitor",
    )
    _ticket(
        "Exam timer stopped",
        "The timer froze on question 7 during the Level 1 exam.",
        "bug",
        "urgent",
        sione,
        Ticket.OPEN,
        6,
    )
    return 6

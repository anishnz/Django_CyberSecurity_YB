"""
services.py - Ticket workflow (state machine), routing, SLA and notifications
=============================================================================

Owner: Rajneesh Kumar (task R-13)

* Routing: Student → their teachers; Teacher → School Admin; School Admin, website
  and email → Super Admin. Super Admin sees all tickets.
* SLA (service time): Urgent 4 hours, High 1 day, Normal 3 days, Low 5 days.
* Allowed status moves are listed in TRANSITIONS (a small state machine).
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.exceptions import AccessDeniedError, ValidationError
from apps.medialib.validators import check_upload

from .models import Ticket, TicketAttachment, TicketComment, TicketHistory

User = get_user_model()
SLA = {"urgent": timedelta(hours=4), "high": timedelta(days=1), "normal": timedelta(days=3), "low": timedelta(days=5)}
TRANSITIONS = {
    Ticket.OPEN: {Ticket.ASSIGNED, Ticket.IN_PROGRESS, Ticket.RESOLVED, Ticket.CLOSED},
    Ticket.ASSIGNED: {Ticket.IN_PROGRESS, Ticket.WAITING, Ticket.RESOLVED, Ticket.CLOSED},
    Ticket.IN_PROGRESS: {Ticket.WAITING, Ticket.RESOLVED, Ticket.CLOSED},
    Ticket.WAITING: {Ticket.IN_PROGRESS, Ticket.RESOLVED, Ticket.CLOSED},
    Ticket.RESOLVED: {Ticket.CLOSED, Ticket.IN_PROGRESS},
    Ticket.CLOSED: {Ticket.IN_PROGRESS},
}
REOPEN_DAYS = 7


def _notify(user_ids, message, ticket) -> None:
    from apps.notifications.services import notify  # pylint: disable=import-outside-toplevel
    notify("ticket_event", {"user_ids": [u for u in user_ids if u], "message": message,
                            "link": f"/tickets/{ticket.pk}/"})


class TicketService:
    """Create, route, comment on and move tickets."""

    # --------------------------------------------------------------- who
    @staticmethod
    def handlers_for(user) -> list[int]:
        """Who should look after a ticket raised by ``user``."""
        if user is None or user.is_super_admin or user.is_school_admin or user.school_id is None:
            return list(User.objects.filter(role="super_admin", is_active=True).values_list("pk", flat=True))
        role = "teacher" if user.is_student else "school_admin"
        ids = list(User.objects.filter(role=role, school_id=user.school_id, is_active=True).values_list("pk", flat=True))
        return ids or list(User.objects.filter(role="super_admin", is_active=True).values_list("pk", flat=True))

    @staticmethod
    def visible_to(user):
        """Tickets a user may see."""
        qs = Ticket.objects.select_related("requester", "assignee", "school")
        if user.is_super_admin:
            return qs
        if user.is_school_admin:
            return qs.filter(Q(school_id=user.school_id) | Q(requester=user))
        if user.is_teacher:
            return qs.filter(Q(requester=user) | Q(assignee=user) | Q(school_id=user.school_id, requester__role="student"))
        return qs.filter(requester=user)

    def can_manage(self, user, ticket) -> bool:
        """Staff who may change status and add internal notes."""
        return user.is_super_admin or (user.role in ("school_admin", "teacher") and ticket.school_id == user.school_id
                                       and ticket.requester_id != user.pk) or ticket.assignee_id == user.pk

    def check_view(self, user, ticket) -> None:
        if not self.visible_to(user).filter(pk=ticket.pk).exists():
            raise AccessDeniedError("You cannot see this ticket.")

    # ------------------------------------------------------------ create
    @transaction.atomic
    def create(self, *, title, description, category="other", priority="normal", requester=None, email="", name="",
               question=None, files=(), request=None) -> Ticket:
        if len((title or "").strip()) < 4:
            raise ValidationError("Please write a short title (at least 4 characters).")
        if len((description or "").strip()) < 10:
            raise ValidationError("Please describe the problem (at least 10 characters).")
        ticket = Ticket.objects.create(
            title=title.strip()[:150], description=description.strip(), category=category, priority=priority,
            requester=requester, requester_email=email or getattr(requester, "email", ""),
            requester_name=name or (requester.get_full_name() if requester else ""),
            school=getattr(requester, "school", None), question=question, sla_due=timezone.now() + SLA[priority])
        if files:
            comment = TicketComment.objects.create(ticket=ticket, author=requester, body="Attachments")
            self._attach(comment, files, request)
        handlers = self.handlers_for(requester)
        _notify(handlers, f"New ticket {ticket.number}: {ticket.title}", ticket)
        self._email_requester(ticket, "ticket_opened")
        return ticket

    def from_contact(self, msg) -> Ticket:
        """Website Contact us form → ticket for the Super Admin."""
        return self.create(title=f"Website: {msg.get_topic_display() if hasattr(msg, 'get_topic_display') else msg.topic}"
                           f" from {msg.name}", description=msg.message, category="contact", email=msg.email,
                           name=msg.name)

    def from_email(self, sender: str, name: str, subject: str, body: str) -> Ticket:
        """Inbound support email (IMAP poller) → ticket."""
        user = User.objects.filter(email__iexact=sender, is_active=True).first()
        return self.create(title=subject or "Email to support", description=body or "(no text)", category="other",
                           requester=user, email=sender, name=name)

    def report_question(self, user, question, note: str) -> Ticket:
        return self.create(title=f"Question {question.code or question.pk} may be wrong",
                           description=note or "A student reported this question.", category="content",
                           requester=user, question=question)

    # ---------------------------------------------------------- comments
    @staticmethod
    def _attach(comment, files, request=None) -> None:
        for f in list(files)[:3]:
            check_upload(f, "attachment", request)
            TicketAttachment.objects.create(comment=comment, file=f, original_name=f.name[:200], size_bytes=f.size)

    @transaction.atomic
    def comment(self, ticket, user, body: str, internal: bool = False, files=(), request=None) -> TicketComment:
        if len((body or "").strip()) < 2:
            raise ValidationError("Please write a reply.")
        if internal and not self.can_manage(user, ticket):
            raise AccessDeniedError("Only staff can add internal notes.")
        comment = TicketComment.objects.create(ticket=ticket, author=user, author_name=str(user), body=body.strip(),
                                               is_internal=internal)
        self._attach(comment, files, request)
        if not internal:
            if user.pk == ticket.requester_id:
                if ticket.status == Ticket.WAITING:
                    self.move(ticket, Ticket.IN_PROGRESS, user, check=False)
                _notify([ticket.assignee_id] if ticket.assignee_id else self.handlers_for(ticket.requester),
                        f"New reply on {ticket.number}", ticket)
            else:
                _notify([ticket.requester_id], f"Reply on your ticket {ticket.number}", ticket)
                self._email_requester(ticket, "ticket_reply", body)
        return comment

    # ------------------------------------------------------------ status
    def move(self, ticket, new_status: str, user, check: bool = True) -> None:
        if check and not self.can_manage(user, ticket) and not (user.pk == ticket.requester_id and new_status == Ticket.CLOSED):
            raise AccessDeniedError("You cannot change this ticket.")
        if new_status not in TRANSITIONS.get(ticket.status, set()):
            raise ValidationError(f"A ticket cannot go from {ticket.get_status_display()} to "
                                  f"{dict(Ticket.STATUSES).get(new_status, new_status)}.")
        if ticket.status == Ticket.CLOSED and ticket.resolved_at and \
                timezone.now() - ticket.resolved_at > timedelta(days=REOPEN_DAYS):
            raise ValidationError(f"Closed tickets can only be reopened within {REOPEN_DAYS} days. Please open a new ticket.")
        old = ticket.status
        ticket.status = new_status
        if new_status in (Ticket.RESOLVED, Ticket.CLOSED) and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        ticket.save()
        TicketHistory.objects.create(ticket=ticket, user=user, field="status", old_value=old, new_value=new_status)
        _notify([ticket.requester_id], f"Ticket {ticket.number} is now {ticket.get_status_display()}", ticket)

    def assign(self, ticket, assignee, user) -> None:
        if not self.can_manage(user, ticket):
            raise AccessDeniedError("You cannot assign this ticket.")
        old = str(ticket.assignee or "")
        ticket.assignee = assignee
        if ticket.status == Ticket.OPEN:
            ticket.status = Ticket.ASSIGNED
        ticket.save()
        TicketHistory.objects.create(ticket=ticket, user=user, field="assignee", old_value=old, new_value=str(assignee))
        _notify([assignee.pk], f"Ticket {ticket.number} was assigned to you", ticket)

    @staticmethod
    def is_overdue(ticket) -> bool:
        return bool(ticket.is_open and ticket.sla_due and timezone.now() > ticket.sla_due)

    @staticmethod
    def _email_requester(ticket, template_key: str, reply: str = "") -> None:
        from apps.emails.services import EmailService  # pylint: disable=import-outside-toplevel
        to = ticket.requester_email or getattr(ticket.requester, "email", "")
        if to:
            EmailService().send_template(template_key, to, {"ticket": ticket.number, "title": ticket.title,
                                                            "name": ticket.requester_name or "there", "reply": reply})

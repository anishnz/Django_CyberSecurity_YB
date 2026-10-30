"""
media.py - Serve uploaded files safely when DEBUG is off
=======================================================

Owner: Anish Shrestha (task A-04, run scripts)

Why: run.bat and run_local.bat use the production settings (DEBUG = False).
Django's ``static()`` helper adds no URLs when DEBUG is False, so uploaded
team photos, meeting photos and school logos showed "404 Not Found". Waitress
has no file server of its own, so Django must serve /media/ itself.

Safety: not every upload is public. Each top folder in MEDIA_ROOT has one rule:

    website/   public (team photos, meeting photos, slider pictures)
    schools/   public (school logos)
    library/   logged in, and the file is in that user's media library;
               students and guests only see published files that are visible to students
    tickets/   only people who can see the ticket; internal notes only for ticket managers
    payslips/  never - payslips are only downloaded through the payments page
    (other)    never

Concepts:
    * Encapsulation: ``MediaAccessPolicy`` keeps every rule in one class.
    * Dispatch table: ``RULES`` maps a folder name to the method that checks it,
      so a new folder needs one line, not a new if/else chain.
"""

from __future__ import annotations

from django.conf import settings
from django.http import Http404
from django.views.static import serve

PUBLIC_FOLDERS = ("website", "schools")


class MediaAccessPolicy:
    """Decides whether a user may open one uploaded file."""

    RULES = {
        "website": "_public",
        "schools": "_public",
        "library": "_library_file",
        "tickets": "_ticket_file",
        "payslips": "_never",
    }

    def allows(self, user, path: str) -> bool:
        """True when ``user`` may open the file at ``path`` (relative to MEDIA_ROOT)."""
        parts = path.replace("\\", "/").split("/")
        if len(parts) < 2 or any(p in ("", ".", "..") for p in parts):
            return False
        rule = self.RULES.get(parts[0], "_never")
        return getattr(self, rule)(user, path)

    # ------------------------------------------------------------------ rules
    @staticmethod
    def _public(_user, _path) -> bool:
        return True

    @staticmethod
    def _never(_user, _path) -> bool:
        return False

    @staticmethod
    def _library_file(user, path) -> bool:
        if not user.is_authenticated:
            return False
        from apps.medialib.services import MediaService  # pylint: disable=import-outside-toplevel

        item = MediaService.visible_to(user).filter(file=path).first()
        if item is None:
            return False
        if user.role in ("student", "guest"):
            return item.is_published and item.visible_to_students
        return True

    @staticmethod
    def _ticket_file(user, path) -> bool:
        if not user.is_authenticated:
            return False
        # pylint: disable=import-outside-toplevel
        from apps.helpdesk.models import TicketAttachment
        from apps.helpdesk.services import TicketService

        attachment = TicketAttachment.objects.select_related("comment__ticket").filter(file=path).first()
        if attachment is None:
            return False
        service = TicketService()
        ticket = attachment.comment.ticket
        if not service.visible_to(user).filter(pk=ticket.pk).exists():
            return False
        return service.can_manage(user, ticket) if attachment.comment.is_internal else True


def serve_media(request, path: str):
    """Send one uploaded file, after the access check. Hidden files look the same as missing files (404)."""
    if not MediaAccessPolicy().allows(request.user, path):
        raise Http404("File not found.")
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    response["X-Content-Type-Options"] = "nosniff"
    if path.split("/", 1)[0] not in PUBLIC_FOLDERS:
        response["Cache-Control"] = "private, no-store"
    return response

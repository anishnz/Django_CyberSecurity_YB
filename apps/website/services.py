"""
services.py - Upload and manage team photos and meeting photos
==============================================================

Owner: Dinesh Upreti (task D-14)

Every upload goes through the same safety check as the media library
(``apps.medialib.validators.check_upload``): the file's first bytes must really be
JPG, PNG, WebP or GIF, and the size must be under the Super Admin's limit.
Every change is written to the audit log.
"""

from __future__ import annotations

from apps.core.services import AuditService
from apps.medialib.validators import check_upload

from .models import MeetingPhoto, TeamMember


class WebsiteContentService:
    """Small service object used by the Website content page (Super Admin)."""

    def __init__(self, user=None, request=None):
        self.user = user
        self.request = request

    # ------------------------------------------------------------------ team
    def update_member(self, member: TeamMember, *, bio: str, photo=None) -> TeamMember:
        """Save a new bio and (optionally) a new photo. The old photo file is removed."""
        member.bio = (bio or "").strip()[:600]
        if photo:
            check_upload(photo, "image", self.request, self.user)
            if member.photo:
                member.photo.delete(save=False)
            member.photo = photo
        member.save()
        AuditService.log(self.user, "team_member_updated", member.name, details="photo" if photo else "bio")
        return member

    def remove_member_photo(self, member: TeamMember) -> None:
        if member.photo:
            member.photo.delete(save=False)
            member.photo = None
            member.save(update_fields=["photo"])
            AuditService.log(self.user, "team_photo_removed", member.name)

    # ------------------------------------------------------------------ meetings
    def add_meeting_photo(self, form) -> MeetingPhoto:
        """Save a MeetingPhotoForm after the file check."""
        check_upload(form.cleaned_data["image"], "image", self.request, self.user)
        photo = form.save()
        AuditService.log(self.user, "meeting_photo_added", photo.title, details=photo.place)
        return photo

    def toggle_meeting_photo(self, photo: MeetingPhoto) -> MeetingPhoto:
        photo.is_active = not photo.is_active
        photo.save(update_fields=["is_active"])
        AuditService.log(self.user, "meeting_photo_shown" if photo.is_active else "meeting_photo_hidden", photo.title)
        return photo

    def delete_meeting_photo(self, photo: MeetingPhoto) -> None:
        title = photo.title
        photo.image.delete(save=False)
        photo.delete()
        AuditService.log(self.user, "meeting_photo_deleted", title)

    # ------------------------------------------------------------------ read
    @staticmethod
    def team():
        return TeamMember.objects.filter(is_active=True)

    @staticmethod
    def meeting_photos():
        return MeetingPhoto.objects.filter(is_active=True)

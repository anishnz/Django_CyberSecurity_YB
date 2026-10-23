"""
services.py - Media library rules: who sees what, uploads, YouTube, cultural check
==================================================================================

Owner: Jihe Qi (task J-12)

* Staff upload images, audio, video and PDFs; the file type is checked by its
  signature and the size by the Super Admin's limits (validators.check_upload).
* Media marked "Has Māori language, images or tikanga" is hidden from students
  until a Cultural Guide (Kaiārahi) ticks the cultural check.
* School media is only seen by that school. Super Admin media is for everyone.
"""

from __future__ import annotations

from django.db.models import Q

from apps.core.exceptions import AccessDeniedError
from apps.core.models import FeatureSwitch
from apps.core.services import AuditService

from .models import MediaFile, VideoEmbed
from .validators import check_upload
from .youtube import video_id


class MediaService:
    """Upload, list and approve media."""

    @staticmethod
    def visible_to(user):
        qs = MediaFile.objects.select_related("topic", "owner", "school")
        return qs if user.is_super_admin else qs.filter(Q(school__isnull=True) | Q(school_id=user.school_id))

    @staticmethod
    def videos_for(user):
        qs = VideoEmbed.objects.select_related("topic", "added_by")
        return qs if user.is_super_admin else qs.filter(Q(school__isnull=True) | Q(school_id=user.school_id))

    @classmethod
    def for_topic(cls, topic, user):
        """What a student sees on a topic page."""
        media = [m for m in cls.visible_to(user).filter(topic=topic, is_published=True) if m.visible_to_students]
        videos = (
            cls.videos_for(user).filter(topic=topic) if FeatureSwitch.is_on("youtube") else VideoEmbed.objects.none()
        )
        return media, videos

    @staticmethod
    def upload(user, form_data: dict, uploaded, request=None) -> MediaFile:
        """Check and save an uploaded file; a Cultural Guide's own upload is checked at once."""
        mime = check_upload(uploaded, form_data["kind"], request, user)
        obj = MediaFile(
            **form_data,
            file=uploaded,
            mime_type=mime,
            size_bytes=uploaded.size,
            owner=user,
            school=None if user.is_super_admin else user.school,
        )
        obj.cultural_check = bool(obj.needs_cultural_check and getattr(user, "is_cultural_guide", False))
        obj.save()
        AuditService.log(user, "media_uploaded", obj.title, new=f"{obj.kind} {obj.size_bytes} bytes")
        return obj

    @staticmethod
    def add_video(user, title: str, url: str, topic=None) -> VideoEmbed:
        vid = video_id(url)
        return VideoEmbed.objects.create(
            title=title.strip()[:120],
            url=url.strip(),
            video_id=vid,
            topic=topic,
            added_by=user,
            school=None if user.is_super_admin else user.school,
        )

    @staticmethod
    def can_change(user, obj) -> bool:
        owner = getattr(obj, "owner_id", None) or getattr(obj, "added_by_id", None)
        return user.is_super_admin or owner == user.pk or (user.is_school_admin and obj.school_id == user.school_id)

    @staticmethod
    def cultural_approve(user, media: MediaFile) -> None:
        """The Kaiārahi gives the cultural check so students can see the file."""
        if not getattr(user, "is_cultural_guide", False):
            raise AccessDeniedError("Only a Cultural Guide (Kaiārahi) can give the cultural check.")
        media.cultural_check = True
        media.save(update_fields=["cultural_check"])
        AuditService.log(user, "media_cultural_check", media.title)

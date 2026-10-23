"""services.py - Who sees which announcement, and who may post. Owner: Rajneesh Kumar."""
from __future__ import annotations

from django.db.models import Q

from apps.core.clock import today
from apps.core.exceptions import AccessDeniedError, ValidationError

from .models import Announcement


class AnnouncementService:
    @staticmethod
    def visible_to(user):
        """Current announcements for this user (date window, school and audience)."""
        now = today()
        qs = Announcement.objects.filter(starts_on__lte=now).filter(Q(ends_on__isnull=True) | Q(ends_on__gte=now))
        if user.is_super_admin:
            return qs
        qs = qs.filter(Q(school__isnull=True) | Q(school_id=user.school_id))
        audience = "students" if user.is_student else "staff"
        return qs.filter(audience__in=["all", audience])

    @staticmethod
    def manageable_by(user):
        if user.is_super_admin:
            return Announcement.objects.all()
        if user.is_school_admin:
            return Announcement.objects.filter(school_id=user.school_id)
        raise AccessDeniedError("Only admins can manage announcements.")

    def save(self, user, obj: Announcement) -> Announcement:
        if not (user.is_super_admin or user.is_school_admin):
            raise AccessDeniedError("Only admins can post announcements.")
        if user.is_school_admin:
            obj.school = user.school
        if obj.ends_on and obj.ends_on < obj.starts_on:
            raise ValidationError("The end date must be after the start date.")
        if obj.pk is None:
            obj.created_by = user
        obj.save()
        return obj

"""signals.py - Django signals that feed the NotificationCenter. Owner: Rajneesh Kumar."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.schools.models import StudentProfile

from .services import notify


@receiver(post_save, sender=StudentProfile)
def section_full_check(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """When a section becomes full, tell the school admins."""
    section = instance.section
    if section is not None and section.student_count == section.capacity:
        notify("section_full", {"school_id": section.school.pk, "section": section.name, "label": section.label})

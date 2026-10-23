"""signals.py - Make sure every school/staff user has the right extra records. Owner: Anish Shrestha."""
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """Every student gets a StudentProfile (section, consent, level)."""
    if instance.role == User.STUDENT:
        from apps.schools.models import StudentProfile  # pylint: disable=import-outside-toplevel
        StudentProfile.objects.get_or_create(user=instance)

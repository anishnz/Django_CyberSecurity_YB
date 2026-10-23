"""services.py - placeholder, replaced in Sprint 3 with the full BIService."""


class BIService:
    """Business intelligence numbers (full version in Sprint 3)."""

    def platform_kpis(self):
        from apps.schools.models import School  # pylint: disable=import-outside-toplevel
        from django.contrib.auth import get_user_model  # pylint: disable=import-outside-toplevel
        User = get_user_model()
        return {"schools": School.objects.filter(is_active=True).count(),
                "students": User.objects.filter(role="student").count(),
                "teachers": User.objects.filter(role="teacher").count()}

    def licences_ending(self, days):  # pylint: disable=unused-argument
        return []

    def pending_payments(self):
        return 0

    def open_tickets(self):
        return 0

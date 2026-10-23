"""context_processors.py - Values every template can use. Owner: Dinesh Upreti."""
from django.conf import settings


def project(request):
    """Project info, menu, bell count and Login-as banner."""
    data = {"project": settings.PROJECT, "demo_mode": settings.DEMO_MODE}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        from apps.notifications.services import unread_count  # pylint: disable=import-outside-toplevel
        from apps.accounts.services import IMPERSONATOR_KEY  # pylint: disable=import-outside-toplevel
        data["menu"] = user.role_obj.menu()
        data["unread_count"] = unread_count(user)
        data["impersonating"] = bool(request.session.get(IMPERSONATOR_KEY))
    return data

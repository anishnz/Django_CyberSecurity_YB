"""panui.py - {% announcements_panel %} shows current announcements on a dashboard. Owner: Dinesh Upreti."""

from django import template

register = template.Library()


@register.inclusion_tag("announcements/_panel.html", takes_context=True)
def announcements_panel(context, limit=3):
    user = context["request"].user
    from apps.announcements.services import AnnouncementService  # pylint: disable=import-outside-toplevel

    return {"items": list(AnnouncementService.visible_to(user)[:limit]) if user.is_authenticated else []}

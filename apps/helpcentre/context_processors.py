"""context_processors.py - The article for the "Explain this page" button. Owner: Dinesh Upreti."""


def page_help(request):
    """Add 'page_help' (the article for the current page) to every template."""
    match = getattr(request, "resolver_match", None)
    user = getattr(request, "user", None)
    if match is None or user is None:
        return {}
    role = user.role if user.is_authenticated else "guest"
    from .services import HelpService  # pylint: disable=import-outside-toplevel

    try:
        return {"page_help": HelpService.for_page(match.view_name, role)}
    except Exception:  # pylint: disable=broad-except  # help must never break a page (e.g. before migrate)
        return {}

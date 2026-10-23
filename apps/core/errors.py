"""errors.py - Friendly 404 and 500 pages. Owner: Anish Shrestha (NFR-02)."""

from django.shortcuts import render


def not_found(request, exception=None):  # pylint: disable=unused-argument
    return render(
        request,
        "core/error.html",
        {"status": 404, "title": "Page not found", "message": "We couldn't find that page."},
        status=404,
    )


def server_error(request):
    return render(
        request,
        "core/error.html",
        {
            "status": 500,
            "title": "Something went wrong",
            "message": "Sorry, something went wrong. The problem has been logged. Please try again.",
        },
        status=500,
    )

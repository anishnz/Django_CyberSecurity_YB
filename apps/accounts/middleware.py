"""
middleware.py - Account status checks on every request
======================================================

Owner: Anish Shrestha (task A-07, A-08)

* AccountStatusMiddleware: logs out a user whose account became inactive,
  expired, or whose school licence ended while they were logged in; blocks
  Demo Guest from changing data (read-only).
* MFARequiredMiddleware: when the Super Admin forces two-step login for admins,
  an admin without MFA is sent to the setup page first.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render

from .services import IMPERSONATOR_KEY, AccountCheck, MFAService

GUEST_POST_ALLOWED = ("/accounts/logout", "/quiz/guest", "/ai/explain", "/website/contact")
MFA_SETUP_ALLOWED = ("/accounts/mfa", "/accounts/logout", "/static", "/media", "/health")


class AccountStatusMiddleware:
    """Keep only valid accounts logged in."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            impersonating = bool(request.session.get(IMPERSONATOR_KEY))
            problem = None if impersonating else AccountCheck.problem(user)
            if problem:
                logout(request)
                messages.error(request, problem)
                return redirect("accounts:login")
            if user.role_obj.read_only and request.method == "POST" and not request.path.startswith(GUEST_POST_ALLOWED):
                return render(
                    request,
                    "core/error.html",
                    {
                        "status": 403,
                        "title": "Read-only",
                        "message": "Demo Guest is read-only. Nothing can be changed.",
                    },
                    status=403,
                )
        return self.get_response(request)


class MFARequiredMiddleware:
    """Send admins to MFA setup when the setting forces it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not request.session.get(IMPERSONATOR_KEY)
            and not request.path.startswith(MFA_SETUP_ALLOWED)
        ):
            try:
                needed = MFAService.required_for(user)
            except Exception:  # pylint: disable=broad-except  # settings table missing during first migrate
                needed = False
            if needed:
                messages.warning(request, "Please set up two-step login (MFA) to keep your admin account safe.")
                return redirect("accounts:mfa_setup")
        return self.get_response(request)

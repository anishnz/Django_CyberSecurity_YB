"""
decorators.py - Access control decorators and mixins (Decorator pattern)
=======================================================================

Owner: Anish Shrestha (task A-07)

Concepts:
    * Decorator pattern: ``@role_required("teacher")`` wraps a view and adds a
      check BEFORE it runs, without changing the view's own code.
    * ``@audit_log("action")`` adds an audit entry AFTER a successful POST.
    * Mixins give class-based views the same checks.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required

from apps.core.exceptions import AccessDeniedError, ReadOnlyError
from apps.core.services import AuditService


def role_required(*roles: str):
    """Allow the view only for users whose role is in ``roles``."""

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                from apps.security.services import SecurityLog  # pylint: disable=import-outside-toplevel
                SecurityLog.record("access_denied", request, request.user, details=f"needs {', '.join(roles)}")
                raise AccessDeniedError()
            return view(request, *args, **kwargs)
        return wrapped

    return decorator


def staff_only(view):
    """Super Admin, School Admin and Teacher only (never students or guests)."""
    return role_required("super_admin", "school_admin", "teacher")(view)


def super_admin_required(view):
    """Super Admin only."""
    return role_required("super_admin")(view)


def not_read_only(view):
    """Block Demo Guest from changing data."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role_obj.read_only and request.method == "POST":
            raise ReadOnlyError()
        return view(request, *args, **kwargs)

    return wrapped


def audit_log(action: str):
    """After a successful POST, write ``action`` and the URL values to the audit log."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            if request.method == "POST" and getattr(response, "status_code", 200) < 400:
                details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                AuditService.log(request.user, action, details or request.path)
            return response
        return wrapped

    return decorator


class RoleRequiredMixin:
    """Class-based view version of @role_required. Set ``allowed_roles``."""

    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        """Check login and role before the view runs."""
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login  # pylint: disable=import-outside-toplevel
            return redirect_to_login(request.get_full_path())
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            raise AccessDeniedError()
        return super().dispatch(request, *args, **kwargs)


def same_school_or_super(user, school) -> None:
    """Raise AccessDeniedError unless the user is Super Admin or belongs to ``school``."""
    if user.is_super_admin:
        return
    if school is None or user.school_id != getattr(school, "pk", school):
        raise AccessDeniedError("You can only see your own school's information.")

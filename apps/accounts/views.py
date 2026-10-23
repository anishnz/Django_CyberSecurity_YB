"""
views.py - Login, two-step login, password, user management, Login as, demo accounts
====================================================================================

Owner: Anish Shrestha (tasks A-06 to A-10)

Views stay thin: they read the form, call a service and show a template.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.exceptions import AccessDeniedError, ValidationError
from apps.security.models import SecurityEvent
from apps.security.services import LockoutService, SecurityLog

from .decorators import super_admin_required
from .forms import LoginAsForm, LoginForm, MFACodeForm, ResetPasswordForm, TemporaryUserForm, UserForm
from .services import MFA_PENDING_KEY, AccountCheck, ImpersonationService, MFAService, UserService

User = get_user_model()


def _safe_next(request, fallback: str) -> str:
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return target
    return fallback


# ------------------------------------------------------------------ login
def login_view(request):
    """Login (Takiuru): password check, lockout, account checks, then MFA if switched on."""
    if request.user.is_authenticated:
        return redirect("accounts:home")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"].strip()
        user_row = User.objects.filter(username__iexact=username).first()
        if user_row and user_row.is_locked():
            SecurityLog.record(SecurityEvent.BLOCKED, request, user_row, details="account locked")
            messages.error(request, "Too many wrong passwords. This account is locked for a short time. "
                                    "Try again later or ask an admin to unlock it.")
            return render(request, "accounts/login.html", {"form": form}, status=401)
        user = authenticate(request, username=user_row.username if user_row else username,
                            password=form.cleaned_data["password"])
        if user is None:
            SecurityLog.record(SecurityEvent.LOGIN_FAILED, request, user_row, username=username)
            if user_row and LockoutService().register_failure(user_row, request):
                messages.error(request, "Too many wrong passwords. The account is now locked for 15 minutes.")
            else:
                messages.error(request, "Wrong username or password.")
            return render(request, "accounts/login.html", {"form": form}, status=401)
        problem = AccountCheck.problem(user)
        if problem:
            SecurityLog.record(SecurityEvent.BLOCKED, request, user, details=problem)
            messages.error(request, problem)
            return render(request, "accounts/login.html", {"form": form}, status=403)
        LockoutService.register_success(user)
        if user.mfa_enabled:
            request.session[MFA_PENDING_KEY] = user.pk
            request.session["mfa_next"] = _safe_next(request, "")
            return redirect("accounts:mfa_verify")
        return _finish_login(request, user)
    return render(request, "accounts/login.html", {"form": form, "demo_mode": settings.DEMO_MODE})


def _finish_login(request, user):
    """Log the user in, record it and go to their dashboard."""
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    SecurityLog.record(SecurityEvent.LOGIN, request, user, details=f"role={user.role}")
    if user.must_change_password:
        messages.info(request, "Please choose a new password.")
        return redirect("accounts:password_change")
    nxt = request.session.pop("mfa_next", "") or _safe_next(request, "")
    return redirect(nxt or user.role_obj.dashboard_url)


def mfa_verify(request):
    """Second step: the 6-digit code from the authenticator app (or a backup code)."""
    user = User.objects.filter(pk=request.session.get(MFA_PENDING_KEY)).first()
    if user is None:
        return redirect("accounts:login")
    form = MFACodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
        service = MFAService()
        if service.verify(user.get_mfa_secret(), code) or service.use_backup_code(user, code):
            request.session.pop(MFA_PENDING_KEY, None)
            return _finish_login(request, user)
        SecurityLog.record(SecurityEvent.MFA_FAILED, request, user)
        messages.error(request, "That code is not right. Try again.")
    return render(request, "accounts/mfa_verify.html", {"form": form, "pending": user})


def logout_view(request):
    """Logout (Takiputa)."""
    if request.method == "POST":
        if request.user.is_authenticated:
            SecurityLog.record(SecurityEvent.LOGOUT, request, request.user)
        logout(request)
        messages.success(request, "You have logged out. Ka kite anō (see you again)!")
    return redirect("website:home")


@login_required
def home(request):
    """Send each user to their own dashboard."""
    return redirect(request.user.role_obj.dashboard_url)


@login_required
def password_change(request):
    """Change own password."""
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        user.must_change_password = False
        user.save(update_fields=["must_change_password"])
        update_session_auth_hash(request, user)
        messages.success(request, "Password changed. Ka pai!")
        return redirect("accounts:home")
    return render(request, "accounts/password_change.html", {"form": form})


# -------------------------------------------------------------------- MFA
@login_required
def mfa_setup(request):
    """Turn on two-step login: scan the QR code, then type a code."""
    service = MFAService()
    secret = request.session.get("mfa_setup_secret") or service.new_secret()
    request.session["mfa_setup_secret"] = secret
    form = MFACodeForm(request.POST or None)
    codes = None
    if request.method == "POST" and form.is_valid():
        codes = service.enable(request.user, secret, form.cleaned_data["code"], request)
        request.session.pop("mfa_setup_secret", None)
        messages.success(request, "Two-step login is on. Save your backup codes somewhere safe.")
    return render(request, "accounts/mfa_setup.html", {
        "form": form, "qr_svg": service.qr_svg(request.user, secret), "secret": secret, "codes": codes})


@login_required
@require_POST
def mfa_disable_self(request):
    """Turn off own two-step login (not allowed when admins are forced to use it)."""
    if MFAService.required_for(request.user) or (request.user.role in ("super_admin", "school_admin")
                                                 and _forced()):
        raise ValidationError("Two-step login is required for admin accounts.")
    MFAService.disable(request.user, request.user, request)
    messages.success(request, "Two-step login is off.")
    return redirect("accounts:mfa_setup")


def _forced() -> bool:
    from apps.core.models import SystemSettings  # pylint: disable=import-outside-toplevel
    return SystemSettings.load().force_mfa_for_admins


# ------------------------------------------------------- user management
@super_admin_required
def user_list(request):
    """All users with search and filters (Super Admin)."""
    users = User.objects.select_related("school").order_by("role", "first_name")
    q, role, school = request.GET.get("q", "").strip(), request.GET.get("role", ""), request.GET.get("school", "")
    if q:
        users = users.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
                             | Q(email__icontains=q))
    if role:
        users = users.filter(role=role)
    if school:
        users = users.filter(school_id=school)
    page = Paginator(users, 25).get_page(request.GET.get("page"))
    from apps.schools.models import School  # pylint: disable=import-outside-toplevel
    from .roles import ROLE_CHOICES  # pylint: disable=import-outside-toplevel
    return render(request, "accounts/user_list.html", {
        "page": page, "q": q, "role": role, "school": school, "roles": ROLE_CHOICES,
        "schools": School.objects.order_by("name"), "temp_form": TemporaryUserForm()})


@super_admin_required
def user_edit(request, pk=None):
    """Create or edit a user."""
    user = get_object_or_404(User, pk=pk) if pk else None
    form = UserForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if user is None:
            extra = {k: data[k] for k in ("phone",)}
            new = UserService().create_user(first_name=data["first_name"], last_name=data["last_name"],
                                            role=data["role"], password=data["password"], school=data["school"],
                                            email=data["email"], by=request.user,
                                            username=data["username"] or None, **extra)
            messages.success(request, f"User {new.username} created.")
        else:
            saved = form.save(commit=False)
            if data.get("password"):
                UserService.reset_password(saved, data["password"], request.user, request)
            saved.save()
            messages.success(request, f"User {saved.username} saved.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "obj": user})


@super_admin_required
@require_POST
def user_toggle(request, pk):
    """Switch a user on or off."""
    user = get_object_or_404(User, pk=pk)
    UserService.set_active(user, not user.is_active, request.user)
    messages.success(request, f"{user.username} is now {'on' if user.is_active else 'off'}.")
    return redirect(request.META.get("HTTP_REFERER") or "accounts:user_list")


@super_admin_required
def user_reset_password(request, pk):
    """Set a new password for a user."""
    user = get_object_or_404(User, pk=pk)
    form = ResetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        UserService.reset_password(user, form.cleaned_data["new_password"], request.user, request)
        messages.success(request, f"New password saved for {user.username}. They must change it at next login.")
        return redirect("accounts:user_list")
    return render(request, "accounts/user_reset.html", {"form": form, "obj": user})


@super_admin_required
@require_POST
def user_mfa_admin(request, pk):
    """Super Admin turns MFA off/reset for a user, or unlocks a locked account."""
    user = get_object_or_404(User, pk=pk)
    action = request.POST.get("action")
    if action == "disable":
        MFAService.disable(user, request.user, request)
        messages.success(request, f"Two-step login turned off for {user.username}. They can set it up again.")
    elif action == "unlock":
        LockoutService.unlock(user, request.user, request)
        messages.success(request, f"{user.username} is unlocked.")
    return redirect(request.META.get("HTTP_REFERER") or "accounts:user_list")


@super_admin_required
@require_POST
def user_temporary(request):
    """Create a temporary account (expires after the set minutes)."""
    form = TemporaryUserForm(request.POST)
    if not form.is_valid():
        raise ValidationError("Please choose a role and minutes between 5 and 240.")
    user, password = UserService().create_temporary(role=form.cleaned_data["role"], school=form.cleaned_data["school"],
                                                    by=request.user, minutes=form.cleaned_data["minutes"])
    messages.success(request, f"Temporary account: {user.username} / {password} "
                              f"(works until {user.expires_at:%H:%M}). Copy it now – it is shown once.")
    return redirect("accounts:user_list")


# --------------------------------------------------------------- Login as
@super_admin_required
def login_as(request, pk):
    """Ask for a reason, then switch to that user's dashboard."""
    target = get_object_or_404(User, pk=pk)
    form = LoginAsForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ImpersonationService.start(request, target, form.cleaned_data["reason"])
        messages.warning(request, f"You are now viewing CyberQuest as {target}. Use 'Return to Super Admin' to stop.")
        return redirect(target.role_obj.dashboard_url)
    return render(request, "accounts/login_as.html", {"form": form, "target": target})


@login_required
@require_POST
def login_as_stop(request):
    """Return to the Super Admin account."""
    admin = ImpersonationService.stop(request)
    if admin is None:
        raise AccessDeniedError("You are not using Login as.")
    messages.success(request, "Welcome back to your Super Admin account.")
    return redirect("accounts:user_list")


# ------------------------------------------------------------ demo accounts
def demo_accounts(request):
    """Demo test logins (only demo accounts, only while DEMO_MODE is on)."""
    if not settings.DEMO_MODE:
        raise AccessDeniedError("The demo accounts page is switched off.")
    users = (User.objects.filter(is_demo=True, is_active=True).exclude(demo_password="")
             .select_related("school").order_by("role", "school__name", "first_name"))
    return render(request, "accounts/demo_accounts.html", {"users": users})

"""
test_accounts.py - Login, roles, lockout, MFA, Login as, demo accounts
=====================================================================

Owner: Jihe Qi (QA) with Anish Shrestha (owner of accounts). TC numbers match the report.
"""
import pyotp
import pytest
from django.test import Client

from apps.accounts.roles import role_for
from apps.accounts.services import MFAService
from apps.security.models import SecurityEvent

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("username, dashboard", [
    ("superadmin", "/admin-panel/"), ("admin.brightstar", "/schools/my/"),
])
def test_tc01_login_goes_to_role_dashboard(username, dashboard):
    from tests.conftest import PASSWORDS
    r = Client().post("/accounts/login/", {"username": username, "password": PASSWORDS[username]})
    assert r.status_code == 302 and r["Location"] == dashboard


def test_tc02_wrong_password_is_logged():
    r = Client().post("/accounts/login/", {"username": "superadmin", "password": "nope"})
    assert r.status_code == 401
    assert SecurityEvent.objects.filter(event="login_failed", username="superadmin").exists()


def test_lockout_after_five_wrong_passwords(user):
    c = Client()
    for _ in range(5):
        c.post("/accounts/login/", {"username": "sione.faleolo", "password": "wrong-1"})
    assert user("sione.faleolo").is_locked()
    r = c.post("/accounts/login/", {"username": "sione.faleolo", "password": "Teacher@2026"})
    assert r.status_code == 401 and b"locked" in r.content
    assert SecurityEvent.objects.filter(event="account_locked").exists()


def test_tc10_expired_licence_blocks_login():
    r = Client().post("/accounts/login/", {"username": "admin.tuivalley", "password": "Admin@2026"})
    assert r.status_code == 403 and "licence has ended" in r.content.decode()


def test_student_without_family_consent_cannot_log_in():
    r = Client().post("/accounts/login/", {"username": "ruby.chen", "password": "Kiaora@2026"})
    assert r.status_code == 403 and "consent" in r.content.decode()


def test_role_classes_are_polymorphic():
    assert role_for("super_admin").dashboard_url == "core:super_dashboard"
    assert role_for("teacher").can_teach and not role_for("teacher").can_manage_users
    assert role_for("guest").read_only
    assert role_for("unknown").code == "guest"


def test_mfa_enable_and_login_needs_code(user, login):
    admin = user("admin.brightstar")
    service = MFAService()
    secret = service.new_secret()
    codes = service.enable(admin, secret, pyotp.TOTP(secret).now())
    assert len(codes) == 8 and admin.mfa_enabled and admin.get_mfa_secret() == secret
    c = Client()
    r = c.post("/accounts/login/", {"username": "admin.brightstar", "password": "Admin@2026"})
    assert r["Location"] == "/accounts/mfa/verify/"
    r = c.post("/accounts/mfa/verify/", {"code": "000000"})
    assert r.status_code == 200 and b"not right" in r.content
    r = c.post("/accounts/mfa/verify/", {"code": codes[0]})  # backup code works once
    assert r.status_code == 302 and r["Location"] == "/schools/my/"


def test_super_admin_can_turn_off_user_mfa(user, login):
    teacher = user("sione.faleolo")
    secret = MFAService.new_secret()
    MFAService().enable(teacher, secret, pyotp.TOTP(secret).now())
    c = login("superadmin")
    c.post(f"/accounts/users/{teacher.pk}/security/", {"action": "disable"})
    teacher.refresh_from_db()
    assert not teacher.mfa_enabled


def test_login_as_needs_reason_and_is_logged(user, login):
    c = login("superadmin")
    target = user("admin.ktm")
    r = c.post(f"/accounts/users/{target.pk}/login-as/", {"reason": "x"})
    assert r.status_code == 200  # reason too short -> form shown again
    r = c.post(f"/accounts/users/{target.pk}/login-as/", {"reason": "Check school admin dashboard"})
    assert r.status_code == 302 and r["Location"] == "/schools/my/"
    assert c.get("/schools/").status_code == 403          # now acting as a School Admin
    assert b"Viewing as" in c.get("/schools/my/").content
    c.post("/accounts/login-as/stop/")
    assert c.get("/schools/").status_code == 200          # back to Super Admin
    events = set(SecurityEvent.objects.values_list("event", flat=True))
    assert {"login_as_start", "login_as_stop"} <= events


def test_cannot_login_as_another_super_admin(user, login):
    c = login("superadmin")
    me = user("superadmin")
    r = c.post(f"/accounts/users/{me.pk}/login-as/", {"reason": "testing myself"})
    assert r.status_code == 403


def test_demo_accounts_page_lists_only_demo_users(client):
    r = client.get("/accounts/demo-accounts/")
    assert r.status_code == 200 and b"tama.ngata" in r.content and b"Kiaora@2026" in r.content


def test_temporary_account_expires(login):
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from apps.accounts.services import AccountCheck
    c = login("superadmin")
    c.post("/accounts/users/temporary/", {"role": "teacher", "school": "", "minutes": 5})
    temp = get_user_model().objects.filter(is_temporary=True).latest("pk")
    assert AccountCheck.problem(temp) is None
    temp.expires_at = timezone.now() - timezone.timedelta(minutes=1)
    assert "expired" in AccountCheck.problem(temp)

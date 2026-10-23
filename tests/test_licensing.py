"""test_licensing.py - Plans, grace period, product keys and Level Pack keys. Owners: Jihe Qi / Rajneesh Kumar."""
from datetime import date

import pytest

from apps.core.exceptions import InvalidLicenseKeyError
from apps.licensing.keys import LicenseKeyValidator
from apps.licensing.plans import BasicPlan, UnlimitedPlan, plan_for
from apps.licensing.services import LevelPackService, LicenseService
from apps.schools.models import School

TODAY = date(2026, 10, 6)


def test_basic_plan_grace_period_and_section_limit():
    plan = BasicPlan(date(2025, 10, 1), date(2026, 10, 1))
    assert plan.is_active(TODAY) and plan.in_grace_period(TODAY)       # 5 days after expiry
    assert not plan.is_active(date(2026, 10, 9))
    assert plan.can_add_section(4) and not plan.can_add_section(5)


def test_unlimited_never_expires_and_discount_halves_price():
    assert UnlimitedPlan(TODAY, date(9999, 12, 31)).is_active(date(2099, 1, 1))
    assert plan_for("STANDARD", TODAY, TODAY, community_discount=True).monthly_price() == 125


def test_key_round_trip_and_tampering():
    v = LicenseKeyValidator("secret")
    key = v.generate("BRIGHTSTAR", "STANDARD", date(2027, 12, 31))
    assert v.parse(key).plan == "STANDARD"
    with pytest.raises(InvalidLicenseKeyError):
        v.parse(key.replace("20271231", "20291231"))                    # edited date
    with pytest.raises(InvalidLicenseKeyError):
        LicenseKeyValidator("other-secret").parse(key)


@pytest.mark.django_db
def test_tc08_product_key_updates_plan():
    school = School.objects.get(code="KAURICOAST")
    key = LicenseKeyValidator().generate("KAURICOAST", "STANDARD", date(2027, 12, 31))
    lic = LicenseService().apply_product_key(school, key)
    assert lic.plan == "STANDARD" and lic.expiry_date == date(2027, 12, 31)


@pytest.mark.django_db
def test_tc09_key_for_another_school_is_rejected():
    key = LicenseKeyValidator().generate("BRIGHTSTAR", "BASIC", date(2027, 12, 31))
    with pytest.raises(InvalidLicenseKeyError):
        LicenseService().apply_product_key(School.objects.get(code="KTMVALLEY"), key)


@pytest.mark.django_db
def test_tc27_level_pack_key():
    ktm = School.objects.get(code="KTMVALLEY")
    key = LicenseKeyValidator().generate("KTMVALLEY", "L3", date(2027, 12, 31))
    LevelPackService().apply_pack_key(ktm, key)
    assert LevelPackService().has_pack(ktm, 3)
    with pytest.raises(InvalidLicenseKeyError):                          # product key in pack box
        LevelPackService().apply_pack_key(ktm, LicenseKeyValidator().generate("KTMVALLEY", "BASIC", date(2027, 1, 1)))


@pytest.mark.django_db
def test_expiry_warning_sent_once_a_day():
    service = LicenseService()
    first = service.expiry_warnings()
    second = service.expiry_warnings()
    assert first >= 1 and second == 0                                  # Bright Star ends in 10 days


@pytest.mark.django_db
def test_students_never_see_prices(login):
    body = login("tama.ngata").get("/quiz/level/1/").content.decode()
    assert "$" not in body

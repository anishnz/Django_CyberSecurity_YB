"""test_integrations.py - Encrypted keys, masking, offline AI, share links, pages. Owner: Jihe Qi (QA)."""

import pytest

from apps.integrations.adapters import ADAPTERS, ShareLinks
from apps.integrations.models import IntegrationSetting
from apps.integrations.services import IntegrationService
from apps.security.models import SecurityEvent

pytestmark = pytest.mark.django_db


def test_key_is_encrypted_masked_and_logged(user):
    row = IntegrationService().save(
        "openai", secret="sk-test-1234567890ABCD", extra={}, enabled=True, user=user("superadmin")
    )
    raw = IntegrationSetting.objects.filter(pk=row.pk).values_list("_secret", flat=True).get()
    assert "sk-test" not in raw and row.get_secret() == "sk-test-1234567890ABCD"
    assert row.masked.endswith("ABCD") and "1234" not in row.masked
    assert SecurityEvent.objects.filter(event="api_key_changed", details="openai").exists()


def test_ai_falls_back_to_offline_without_keys():
    ai = IntegrationService().ai()
    assert ai.provider == "offline"
    text = ai.generate("Write a QUESTION. TOPIC: phishing emails")
    assert "Answer: B" in text


def test_test_connection_without_key_reports_problem():
    ok, msg = IntegrationService().test("claude")
    assert not ok and "No key" in msg
    assert IntegrationSetting.objects.get(provider="claude").status == "error"


def test_free_share_links_need_no_key():
    assert ShareLinks.whatsapp("Kia ora").startswith("https://wa.me/?text=Kia%20ora")
    assert "sharer.php?u=https%3A%2F%2F" in ShareLinks.facebook("https://cyberquest.local/")
    assert all(p in ADAPTERS for p in ("gmail", "google_maps", "whatsapp", "viber", "share"))


def test_status_summary_used_by_health_check():
    summary = IntegrationService().status_summary()
    assert "gmail" in summary and "offline" not in summary


def test_pages_super_admin_only(login):
    admin = login("superadmin")
    assert admin.get("/integrations/").status_code == 200
    assert admin.get("/integrations/ai-test/").status_code == 200
    r = admin.post("/integrations/ai-test/", {"provider": "offline", "prompt": "TOPIC: strong passwords"})
    assert r.status_code == 200 and b"passphrase" in r.content
    assert login("sione.faleolo").get("/integrations/").status_code == 403

"""
test_api.py - JSON API for React and the API check page
=======================================================

Owner: Jihe Qi (QA, tasks J-15 and J-16)
"""

from __future__ import annotations

import pytest

from apps.integrations.adapters import ADAPTERS

pytestmark = pytest.mark.django_db

PUBLIC = [
    "/api/v1/",
    "/api/v1/health/",
    "/api/v1/levels/",
    "/api/v1/plans/",
    "/api/v1/team/",
    "/api/v1/meeting-photos/",
]


@pytest.mark.parametrize("url", PUBLIC)
def test_public_endpoints_answer_with_the_same_envelope(client, url):
    r = client.get(url)
    body = r.json()
    assert r.status_code == 200 and body["ok"] is True and "data" in body and isinstance(body["ms"], int)


def test_levels_and_plans_content(client):
    levels = client.get("/api/v1/levels/").json()["data"]
    assert [lvl["number"] for lvl in levels] == [1, 2, 3, 4, 5, 6] and levels[0]["is_free"]
    plans = {p["code"]: p for p in client.get("/api/v1/plans/").json()["data"]["plans"]}
    assert plans["STANDARD"]["monthly_nzd"] == 250 and plans["STANDARD"]["monthly_community_nzd"] == 125


def test_cors_only_for_listed_react_origin(client, settings):
    settings.API_CORS_ORIGINS = ["http://localhost:5173"]
    ok = client.get("/api/v1/levels/", HTTP_ORIGIN="http://localhost:5173")
    assert ok["Access-Control-Allow-Origin"] == "http://localhost:5173"
    other = client.get("/api/v1/levels/", HTTP_ORIGIN="https://evil.example")
    assert "Access-Control-Allow-Origin" not in other
    preflight = client.options("/api/v1/levels/", HTTP_ORIGIN="http://localhost:5173")
    assert preflight.status_code == 204


def test_integration_endpoints_need_super_admin(client, login):
    assert client.get("/api/v1/integrations/").status_code == 401
    r = login("sione.faleolo").get("/api/v1/integrations/")
    assert r.status_code == 403 and r.json()["error"] == "Only the Super Admin can use this endpoint."


def test_integration_status_never_sends_keys(login):
    rows = login("superadmin").get("/api/v1/integrations/").json()["data"]
    providers = {r["provider"] for r in rows}
    assert {"claude", "openai", "gemini", "offline"} <= providers
    assert all("secret" not in r and "key" not in r for r in rows)


def test_check_offline_helper_connects(login):
    body = login("superadmin").post("/api/v1/integrations/offline/test/").json()
    assert body["ok"] and body["data"]["connected"] is True


def test_check_ai_model_without_key_says_so(login):
    body = login("superadmin").post("/api/v1/integrations/claude/test/").json()
    assert body["ok"] and body["data"]["connected"] is False and "No key saved" in body["data"]["message"]


def test_unknown_provider_is_404(login):
    r = login("superadmin").post("/api/v1/integrations/nope/test/")
    assert r.status_code == 404 and r.json()["ok"] is False


def test_test_endpoint_needs_csrf_token():
    from django.test import Client  # pylint: disable=import-outside-toplevel

    strict = Client(enforce_csrf_checks=True)
    assert strict.post("/api/v1/integrations/offline/test/").status_code == 403


def test_api_check_page_has_a_check_button_per_row(login, client):
    assert client.get("/api/check/").status_code == 302
    page = login("superadmin").get("/api/check/").content.decode()
    # 6 data endpoints + one row per integration (11 since DeepSeek and Other AI were added)
    assert page.count("data-api-row") == 6 + len(ADAPTERS) and page.count("data-check>") >= 6 + len(ADAPTERS)
    assert "Connect from React" in page and "api_check.js" in page

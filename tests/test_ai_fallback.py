"""test_ai_fallback.py - AI models: DeepSeek, Other AI, order, default, automatic switching, WhatsApp test.

Owner: Jihe Qi (QA, task J-14). No real keys are used: requests.post is replaced by a fake
that answers like each service (Gemini, DeepSeek, Claude, OpenAI, WhatsApp).
"""

from __future__ import annotations

import pytest

from apps.core.exceptions import ValidationError
from apps.core.models import FeatureSwitch
from apps.integrations import adapters
from apps.integrations.adapters import (
    AI_ORDER,
    CustomAIProvider,
    DeepSeekProvider,
    FallbackAIProvider,
    GeminiProvider,
    OfflineTemplateProvider,
)
from apps.integrations.models import IntegrationSetting
from apps.integrations.services import IntegrationService

pytestmark = pytest.mark.django_db


class FakeResponse:
    """Just enough of requests.Response for the adapters."""

    def __init__(self, status: int, data: dict | None = None):
        self.status_code, self._data = status, data or {}
        self.ok = 200 <= status < 300

    def json(self):
        return self._data


def openai_answer(text):
    return FakeResponse(200, {"choices": [{"message": {"content": text}}]})


def gemini_answer(text):
    return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": text}]}}]})


@pytest.fixture(name="fake_http")
def fake_http_fixture(monkeypatch):
    """fake_http({'generativelanguage': FakeResponse(429), 'deepseek': ...}) -> list of called URLs."""
    calls: list[tuple[str, dict]] = []

    def install(answers: dict[str, FakeResponse]):
        def fake_post(url, **kw):
            calls.append((url, kw))
            for part, response in answers.items():
                if part in url:
                    return response
            raise AssertionError(f"unexpected URL {url}")

        monkeypatch.setattr(adapters.requests, "post", fake_post)
        return calls

    return install


@pytest.fixture(name="ai_on")
def ai_on_fixture():
    FeatureSwitch.objects.filter(key="ai").update(enabled=True)


def switch_on(provider: str, key: str = "test-key", **extra):
    service = IntegrationService()
    service.save(provider, secret=key, extra=extra, enabled=True)
    return service


# ----------------------------------------------------------------- order and default
def test_default_order_is_gemini_then_deepseek():
    assert AI_ORDER[:2] == ["gemini", "deepseek"]
    assert IntegrationService().ai_order() == AI_ORDER


def test_default_model_goes_first_and_order_numbers_count(user):
    service = IntegrationService()
    service.save_ai_settings(
        order={"gemini": 10, "deepseek": 20, "claude": 5, "openai": 30, "custom_ai": 40},
        default="openai",
        switched_on={"gemini", "openai"},
        user=user("superadmin"),
    )
    assert service.ai_order()[:3] == ["openai", "claude", "gemini"]
    assert IntegrationSetting.objects.get(provider="openai").is_default
    assert set(IntegrationSetting.objects.filter(enabled=True).values_list("provider", flat=True)) == {
        "gemini",
        "openai",
    }


def test_order_numbers_must_be_1_to_99():
    with pytest.raises(ValidationError):
        IntegrationService().save_ai_settings(order={"gemini": 0}, default="", switched_on=set())


def test_no_model_on_means_offline_helper(ai_on):  # pylint: disable=unused-argument
    assert isinstance(IntegrationService().ai(), OfflineTemplateProvider)


# ----------------------------------------------------------------- automatic switching
def test_gemini_out_of_free_tokens_switches_to_deepseek(fake_http, ai_on):  # pylint: disable=unused-argument
    switch_on("gemini")
    switch_on("deepseek")
    calls = fake_http({"generativelanguage": FakeResponse(429), "deepseek": openai_answer("Stop and think.")})
    ai = IntegrationService().ai()
    assert isinstance(ai, FallbackAIProvider)
    assert ai.generate("TOPIC: phishing") == "Stop and think."
    assert ai.label == "DeepSeek"
    assert [ok for _label, ok, _msg in ai.attempts] == [False, True]
    assert "free tokens" in ai.attempts[0][2]
    assert "generativelanguage" in calls[0][0] and "deepseek" in calls[1][0]
    gemini = IntegrationSetting.objects.get(provider="gemini")
    assert gemini.status == "error" and "429" in gemini.last_error  # saved on the card
    assert IntegrationSetting.objects.get(provider="deepseek").status == "connected"


def test_every_model_fails_then_offline_helper_answers(fake_http, ai_on):  # pylint: disable=unused-argument
    switch_on("gemini")
    switch_on("deepseek")
    fake_http({"generativelanguage": FakeResponse(503), "deepseek": FakeResponse(402)})
    ai = IntegrationService().ai()
    text = ai.generate("TOPIC: strong passwords")
    assert text and ai.used.provider == "offline"
    assert "no credit left" in ai.attempts[1][2]


def test_network_error_also_switches(monkeypatch, ai_on):  # pylint: disable=unused-argument
    switch_on("gemini")

    def no_internet(*_a, **_k):
        raise adapters.requests.ConnectionError("down")

    monkeypatch.setattr(adapters.requests, "post", no_internet)
    ai = IntegrationService().ai()
    assert ai.generate("TOPIC: scams") and ai.used.provider == "offline"
    assert "Could not reach" in ai.attempts[0][2]


def test_ai_switch_off_means_offline_even_with_keys():
    switch_on("gemini")
    FeatureSwitch.objects.filter(key="ai").update(enabled=False)
    assert isinstance(IntegrationService().ai(), OfflineTemplateProvider)


# ----------------------------------------------------------------- providers
def test_deepseek_uses_openai_format_with_bearer_key(fake_http):
    calls = fake_http({"deepseek": openai_answer("OK")})
    assert DeepSeekProvider("sk-test").generate("hi", 10) == "OK"
    url, kw = calls[0]
    assert url == "https://api.deepseek.com/chat/completions"
    assert kw["headers"]["Authorization"] == "Bearer sk-test" and kw["json"]["model"] == "deepseek-chat"


def test_gemini_sends_key_in_header_not_in_url(fake_http):
    calls = fake_http({"generativelanguage": gemini_answer("OK")})
    assert GeminiProvider("AIza-test").generate("hi", 10) == "OK"
    url, kw = calls[0]
    assert "key=" not in url and kw["headers"]["x-goog-api-key"] == "AIza-test"


def test_other_ai_works_without_a_key_and_shows_its_name(fake_http):
    calls = fake_http({"localhost:11434": openai_answer("OK")})
    ai = CustomAIProvider("", {"display_name": "Ollama", "base_url": "http://localhost:11434/v1/", "model": "llama3"})
    assert ai.label == "Ollama (Other AI)"
    assert ai.generate("hi", 10) == "OK"
    assert calls[0][0] == "http://localhost:11434/v1/chat/completions"
    assert "Authorization" not in calls[0][1]["headers"]


def test_other_ai_without_address_explains_what_is_missing():
    ok, message = CustomAIProvider().test_connection()
    assert not ok and "API address" in message


def test_check_button_asks_a_tiny_real_question(fake_http):
    fake_http({"deepseek": openai_answer("OK")})
    switch_on("deepseek")
    ok, message = IntegrationService().test("deepseek")
    assert ok and "answered in" in message and "OK" in message


def test_wrong_key_gives_a_clear_message(fake_http):
    fake_http({"deepseek": FakeResponse(401)})
    ok, message = DeepSeekProvider("bad").test_connection()
    assert not ok and message == "DeepSeek said 401: the key was not accepted."


# ----------------------------------------------------------------- pages
def test_ai_models_page_is_super_admin_only(login):
    assert login("superadmin").get("/integrations/ai-models/").status_code == 200
    assert login("sione.faleolo").get("/integrations/ai-models/").status_code in (302, 403)


def test_ai_models_page_saves_default_and_order(login):
    client = login("superadmin")
    data = {f"order-{n}": i for i, n in enumerate(AI_ORDER, start=1)} | {"default": "deepseek", "on-deepseek": "on"}
    response = client.post("/integrations/ai-models/", data)
    assert response.status_code == 302
    assert IntegrationService().ai_order()[0] == "deepseek"
    assert IntegrationSetting.objects.get(provider="deepseek").enabled


def test_ai_test_page_shows_the_switch(login, fake_http, ai_on):  # pylint: disable=unused-argument
    switch_on("gemini")
    switch_on("deepseek")
    fake_http({"generativelanguage": FakeResponse(429), "deepseek": openai_answer("Be careful online.")})
    page = login("superadmin").post("/integrations/ai-test/", {"provider": "auto", "prompt": "TOPIC: scams"})
    html = page.content.decode()
    assert "Be careful online." in html and "→ next model" in html and "Answered by: <strong>DeepSeek" in html


# ----------------------------------------------------------------- WhatsApp
@pytest.mark.parametrize("raw", ["021 123 4567", "+64", "abc", "+64 21 123 4567 8899 00"])
def test_whatsapp_phone_must_be_international(raw):
    with pytest.raises(ValidationError):
        IntegrationService.clean_phone(raw)


def test_whatsapp_test_sends_the_template(fake_http, user):
    calls = fake_http({"graph.facebook.com": FakeResponse(200, {"messages": [{"id": "wamid.TEST"}]})})
    switch_on("whatsapp", key="EAAG-token", phone_number_id="123456")
    message_id = IntegrationService().whatsapp_test("+64 21 123 4567", user=user("superadmin"))
    url, kw = calls[0]
    assert message_id == "wamid.TEST" and url.endswith("/123456/messages")
    assert kw["json"]["to"] == "64211234567"
    assert kw["json"]["type"] == "template" and kw["json"]["template"]["name"] == "hello_world"


def test_whatsapp_test_page_is_super_admin_only(login):
    response = login("sione.faleolo").post("/integrations/whatsapp/send-test/", {"phone": "+64211234567"})
    assert response.status_code in (302, 403)
    response = login("superadmin").post("/integrations/whatsapp/send-test/", {"phone": "+64211234567"})
    assert response.status_code == 302  # no token saved -> friendly error message, nothing sent

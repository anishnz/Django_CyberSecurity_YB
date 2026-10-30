"""
adapters.py - One class per outside service (Adapter pattern)
=============================================================

Owner: Jihe Qi (task J-10)

Every service looks different on the outside (Gemini, DeepSeek, Claude, OpenAI, Gmail,
WhatsApp, Viber …). Each adapter gives CyberQuest the SAME small interface:

    test_connection() -> (ok, message)
    AI adapters:        generate(prompt, max_tokens) -> text
    Message adapters:   send(to, text) -> message id
    Share adapters:     share_url(text, url) -> link   (free, no key needed)

The app works fully without any of them (offline fallback).
Endpoints and model names are settings, so they can be changed without code.
"""

from __future__ import annotations

import imaplib
import smtplib
import textwrap
import time
from abc import ABC, abstractmethod
from urllib.parse import quote, urlencode

import requests

from apps.core.exceptions import IntegrationError

TIMEOUT = 15


class Adapter(ABC):
    """Common parent: every adapter knows its provider name and settings."""

    provider = ""
    label = ""
    kind = ""  # ai / email / maps / message / share
    needs_secret = True
    secret_label = "API key"
    extra_fields: list[tuple[str, str, str]] = []  # (key, label, default)
    help_text = ""

    def __init__(self, secret: str = "", extra: dict | None = None):
        self.secret = secret or ""
        self.extra = {k: v for k, _, v in self.extra_fields} | (extra or {})

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Check the settings work. Never raises – returns (ok, message)."""

    def _get(self, url, **kw):
        try:
            return requests.get(url, timeout=TIMEOUT, **kw)
        except requests.RequestException as exc:
            raise IntegrationError(f"Could not reach {self.label}: {exc.__class__.__name__}") from exc

    def _post(self, url, **kw):
        try:
            return requests.post(url, timeout=TIMEOUT, **kw)
        except requests.RequestException as exc:
            raise IntegrationError(f"Could not reach {self.label}: {exc.__class__.__name__}") from exc

    def _safe_test(self, func) -> tuple[bool, str]:
        if self.needs_secret and not self.secret:
            return False, "No key saved yet."
        try:
            return func()
        except IntegrationError as exc:
            return False, exc.message
        except Exception as exc:  # pylint: disable=broad-except
            return False, f"{exc.__class__.__name__}: {str(exc)[:120]}"


# ------------------------------------------------------------------------ AI
HTTP_REASONS = {
    400: "the request was refused - check the model name",
    401: "the key was not accepted",
    402: "no credit left on this account",
    403: "the key was not accepted or has no access",
    404: "model or API address not found",
    408: "the service took too long",
    429: "free tokens or the rate limit are used up for now",
}


class AIProvider(Adapter):
    """Parent for AI text generators.

    Template Method: ``test_connection()`` is written once here. It asks the model a tiny
    question through the child's own ``generate()``, so a test proves the key works AND
    that tokens are still available - not only that the key is saved.
    """

    kind = "ai"
    TEST_PROMPT = "Reply with one word: OK"

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        """Return generated text, or raise IntegrationError."""

    def test_connection(self) -> tuple[bool, str]:
        def run():
            start = time.monotonic()
            text = self.generate(self.TEST_PROMPT, max_tokens=60)
            seconds = time.monotonic() - start
            sample = text.strip().splitlines()[0][:40] if text.strip() else "(empty answer)"
            return True, f"{self.label} answered in {seconds:.1f} s: {sample}"

        return self._safe_test(run)

    def _fail(self, response) -> IntegrationError:
        """Turn an HTTP error into a short message a Super Admin can act on.

        The service's own error text is added when there is one (for example Google answers
        400 'API key not valid' for a wrong key, and DeepSeek answers 402 'Insufficient Balance').
        """
        code = response.status_code
        detail = self._error_text(response)
        if code == 400 and "api key" in detail.lower():
            reason = HTTP_REASONS[401]  # Google uses 400 for a wrong key
        else:
            reason = HTTP_REASONS.get(code, "the service is busy or down" if code >= 500 else "unexpected answer")
        message = f"{self.label} said {code}: {reason}."
        if detail:
            message += f" ({detail[:120]})"
        return IntegrationError(message)

    @staticmethod
    def _error_text(response) -> str:
        """The 'error.message' text that OpenAI-style, DeepSeek, Claude and Google APIs send back."""
        try:
            data = response.json()
        except ValueError:
            return ""
        error = data.get("error") if isinstance(data, dict) else None
        if isinstance(error, dict):
            return str(error.get("message", "")).strip()
        return str(error or "").strip()


class OfflineTemplateProvider(AIProvider):
    """No internet and no key: builds simple, safe drafts from templates."""

    provider, label, needs_secret = "offline", "Offline helper (no AI key)", False
    help_text = "Always available. Makes simple template drafts so the app works without internet."

    def test_connection(self):
        return True, "Offline helper is always ready."

    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        topic = (
            prompt.split("TOPIC:", 1)[-1].strip().splitlines()[0][:120] if "TOPIC:" in prompt else "staying safe online"
        )
        if "QUESTION" in prompt.upper():
            return (
                f"Question: What is the SAFEST thing to do about {topic}?\n"
                "A: Ignore it and hope for the best\nB: Stop, think and ask a trusted adult\n"
                "C: Share it with friends straight away\nD: Click the link to find out more\n"
                "Answer: B\nFeedback: When something online feels wrong, stop and talk to a trusted adult first."
            )
        return textwrap.shorten(
            f"{topic.capitalize()}: stop and think before you click, keep personal "
            "information private, use strong passphrases, and talk to a trusted adult "
            "(a teacher or your whānau) if something feels wrong.",
            width=max(80, max_tokens * 4),
        )


class OpenAICompatibleProvider(AIProvider):
    """Parent for every service that speaks the OpenAI 'chat completions' format.

    Inheritance: OpenAI, DeepSeek and the custom 'Other AI' card only change their
    class attributes (name, address, model) - the HTTP code is written once here.
    """

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.secret:
            headers["Authorization"] = f"Bearer {self.secret}"
        return headers

    def _base(self) -> str:
        base = (self.extra.get("base_url") or "").strip().rstrip("/")
        if not base:
            raise IntegrationError(f"{self.label}: add the API address first.")
        return base

    def generate(self, prompt, max_tokens=400):
        base = self._base()
        if not (self.extra.get("model") or "").strip():
            raise IntegrationError(f"{self.label}: add the model name first.")
        r = self._post(
            f"{base}/chat/completions",
            headers=self._headers(),
            json={
                "model": self.extra["model"].strip(),
                "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            },
        )
        if not r.ok:
            raise self._fail(r)
        try:
            text = r.json()["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise IntegrationError(f"{self.label} sent an answer we could not read.") from exc
        return text.strip()


class OpenAIProvider(OpenAICompatibleProvider):
    """OpenAI chat completions."""

    provider, label = "openai", "OpenAI"
    extra_fields = [("model", "Model", "gpt-4o-mini"), ("base_url", "API address", "https://api.openai.com/v1")]
    help_text = "Create a key at platform.openai.com → API keys. Usage is charged by OpenAI."


class DeepSeekProvider(OpenAICompatibleProvider):
    """DeepSeek chat API (OpenAI-compatible)."""

    provider, label = "deepseek", "DeepSeek"
    extra_fields = [("model", "Model", "deepseek-chat"), ("base_url", "API address", "https://api.deepseek.com")]
    help_text = (
        "Create a key at platform.deepseek.com → API keys. Usage is paid from a prepaid balance; "
        "when the balance is empty DeepSeek answers 402 and CyberQuest moves to the next model."
    )


class CustomAIProvider(OpenAICompatibleProvider):
    """'Other AI': any OpenAI-compatible service, for example OpenRouter, Groq, Mistral or a local Ollama."""

    provider, label = "custom_ai", "Other AI (OpenAI-compatible)"
    needs_secret = False  # a local model (Ollama) needs no key
    secret_label = "API key (leave empty for a local model)"
    extra_fields = [
        ("display_name", "Name shown in CyberQuest", "Other AI"),
        ("base_url", "API address (ends before /chat/completions)", ""),
        ("model", "Model", ""),
    ]
    help_text = (
        "Any service that uses the OpenAI format. Examples: OpenRouter https://openrouter.ai/api/v1, "
        "Groq https://api.groq.com/openai/v1, Mistral https://api.mistral.ai/v1, "
        "local Ollama http://localhost:11434/v1 (no key)."
    )

    def __init__(self, secret: str = "", extra: dict | None = None):
        super().__init__(secret, extra)
        name = (self.extra.get("display_name") or "").strip()
        if name and name.lower() != "other ai":
            self.label = f"{name} (Other AI)"


class ClaudeProvider(AIProvider):
    """Anthropic Claude messages API."""

    provider, label = "claude", "Claude (Anthropic)"
    extra_fields = [
        ("model", "Model", "claude-haiku-4-5-20251001"),
        ("base_url", "API address", "https://api.anthropic.com/v1"),
    ]
    help_text = "Create a key at console.anthropic.com → API keys. Usage is charged by Anthropic."

    def _headers(self):
        return {"x-api-key": self.secret, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    def generate(self, prompt, max_tokens=400):
        r = self._post(
            f"{self.extra['base_url'].rstrip('/')}/messages",
            headers=self._headers(),
            json={
                "model": self.extra["model"],
                "max_tokens": max_tokens,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if not r.ok:
            raise self._fail(r)
        return "".join(part.get("text", "") for part in r.json().get("content", [])).strip()


class GeminiProvider(AIProvider):
    """Google Gemini generateContent API."""

    provider, label = "gemini", "Google Gemini"
    extra_fields = [
        ("model", "Model", "gemini-2.5-flash"),
        ("base_url", "API address", "https://generativelanguage.googleapis.com/v1beta"),
    ]
    help_text = (
        "Create a key at aistudio.google.com → Get API key. The free tier has a daily limit; "
        "when it is used up Google answers 429 and CyberQuest moves to the next model."
    )

    def generate(self, prompt, max_tokens=400):
        config: dict = {"maxOutputTokens": max_tokens}
        if self.extra["model"].startswith("gemini-2.5-flash"):
            config["thinkingConfig"] = {"thinkingBudget": 0}  # short drafts: spend tokens on the answer
        r = self._post(
            f"{self.extra['base_url'].rstrip('/')}/models/{self.extra['model']}:generateContent",
            headers={"x-goog-api-key": self.secret},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": config,
            },
        )
        if not r.ok:
            raise self._fail(r)
        try:
            parts = r.json()["candidates"][0]["content"].get("parts", [])
        except (KeyError, IndexError, ValueError) as exc:
            raise IntegrationError("Google Gemini sent no answer (it may have been blocked).") from exc
        return "".join(p.get("text", "") for p in parts).strip()


class FallbackAIProvider(AIProvider):
    """Tries each switched-on model in order; the offline helper is always last.

    Chain of Responsibility: every model gets a chance to answer. When one fails
    (free tokens used up, no credit, wrong key, no internet, server down) the next one
    tries. ``attempts`` keeps what happened so the AI test page can show it.
    """

    provider, needs_secret = "auto", False

    def __init__(self, providers: list[AIProvider], on_result=None):
        super().__init__()
        self.providers = [p for p in providers if p.provider != "offline"] + [OfflineTemplateProvider()]
        self.on_result = on_result  # callback(provider_name, ok, message) - saves the status on the card
        self.used: AIProvider | None = None
        self.attempts: list[tuple[str, bool, str]] = []

    @property
    def label(self) -> str:  # pylint: disable=invalid-overridden-method
        if self.used is not None:
            return self.used.label
        return "Automatic: " + " → ".join(p.label for p in self.providers)

    def generate(self, prompt, max_tokens=400):
        self.attempts, self.used = [], None
        for ai in self.providers:
            start = time.monotonic()
            try:
                text = ai.generate(prompt, max_tokens=max_tokens)
                if not text.strip():
                    raise IntegrationError(f"{ai.label} sent an empty answer.")
            except IntegrationError as exc:
                self._note(ai, False, exc.message)
                continue
            except Exception as exc:  # pylint: disable=broad-except
                self._note(ai, False, f"{ai.label}: {exc.__class__.__name__}")
                continue
            self._note(ai, True, f"answered in {time.monotonic() - start:.1f} s")
            self.used = ai
            return text
        raise IntegrationError("No AI model could answer.")  # not reached: the offline helper always answers

    def test_connection(self):
        return True, f"{len(self.providers)} models in order: " + " → ".join(p.label for p in self.providers)

    def _note(self, ai: AIProvider, ok: bool, message: str) -> None:
        self.attempts.append((ai.label, ok, message))
        if self.on_result and ai.provider != "offline":
            self.on_result(ai.provider, ok, message)


SYSTEM_PROMPT = (
    "You help New Zealand school teachers write short, kind, accurate cyber-safety learning text for "
    "children. Use simple English. Never include real people's names or personal details. "
    "Do not invent te reo Māori words; leave Māori wording for the Cultural Guide to add."
)


# --------------------------------------------------------------------- email
class GmailAdapter(Adapter):
    """Gmail SMTP (send) and IMAP (read for auto-reply) with an App Password."""

    provider, label, kind = "gmail", "Gmail (SMTP + IMAP)", "email"
    secret_label = "App Password (16 characters)"
    extra_fields = [
        ("address", "Gmail address", ""),
        ("sender_name", "Sender name", "CyberQuest"),
        ("smtp_host", "SMTP server", "smtp.gmail.com"),
        ("smtp_port", "SMTP port", "587"),
        ("imap_host", "IMAP server", "imap.gmail.com"),
    ]
    help_text = (
        "Turn on 2-Step Verification in your Google Account, then create an App Password "
        "(Google Account → Security → App passwords). Normal Gmail sends about 500 emails a day."
    )

    def test_connection(self):
        def run():
            with smtplib.SMTP(self.extra["smtp_host"], int(self.extra["smtp_port"]), timeout=TIMEOUT) as s:
                s.starttls()
                s.login(self.extra["address"], self.secret)
            return True, "Signed in to Gmail SMTP."

        return self._safe_test(run)

    def imap(self) -> imaplib.IMAP4_SSL:
        box = imaplib.IMAP4_SSL(self.extra["imap_host"], 993, timeout=TIMEOUT)
        box.login(self.extra["address"], self.secret)
        return box


# ---------------------------------------------------------------------- maps
class GoogleMapsAdapter(Adapter):
    """Google Maps Embed API (the key is used in the browser iframe)."""

    provider, label, kind = "google_maps", "Google Maps", "maps"
    help_text = "Create a key in Google Cloud Console and enable the 'Maps Embed API'. Restrict it to your website."

    def test_connection(self):
        def run():
            ok = len(self.secret) >= 30 and self.secret.startswith("AIza")
            return (
                (True, "Key saved. The map loads in the browser.")
                if ok
                else (False, "This does not look like a Google API key.")
            )

        return self._safe_test(run)

    def embed_url(self, query: str) -> str:
        if self.secret:
            return "https://www.google.com/maps/embed/v1/place?" + urlencode({"key": self.secret, "q": query})
        return ""


# ------------------------------------------------------------------ messages
class MessageAdapter(Adapter):
    """Parent for WhatsApp / Viber: automatic messages (paid business APIs)."""

    kind = "message"

    @abstractmethod
    def send(self, to: str, text: str) -> str:
        """Send a text; return the provider's message id."""


class WhatsAppAdapter(MessageAdapter):
    """WhatsApp Business Cloud API (Meta Graph API)."""

    provider, label = "whatsapp", "WhatsApp Business (Cloud API)"
    secret_label = "Access token"
    extra_fields = [
        ("phone_number_id", "Phone number ID", ""),
        ("api_version", "Graph API version", "v20.0"),
        ("template_name", "Test template name", "hello_world"),
        ("template_lang", "Test template language", "en_US"),
    ]
    help_text = (
        "Needs a Meta business account and the WhatsApp Business Platform (developers.facebook.com → WhatsApp → "
        "API Setup gives the Phone number ID and a token). Business-started messages need approved templates and "
        "are charged per message. Parents must opt in. 'hello_world' is Meta's ready-made test template."
    )

    def _url(self, path=""):
        return f"https://graph.facebook.com/{self.extra['api_version']}/{self.extra['phone_number_id']}{path}"

    def test_connection(self):
        def run():
            r = self._get(self._url(), headers={"Authorization": f"Bearer {self.secret}"})
            return (True, "Connected to WhatsApp.") if r.ok else (False, f"Meta said {r.status_code}.")

        return self._safe_test(run)

    def send(self, to, text):
        """Free text. Meta only delivers it inside 24 hours after the person last messaged us."""
        return self._send({"type": "text", "text": {"body": text[:4000]}}, to)

    def send_template(self, to: str, name: str = "", lang: str = "") -> str:
        """An approved template (works at any time). Used by the Super Admin's test message."""
        template = {
            "name": name or self.extra["template_name"],
            "language": {"code": lang or self.extra["template_lang"]},
        }
        return self._send({"type": "template", "template": template}, to)

    def _send(self, body: dict, to: str) -> str:
        if not self.secret or not self.extra.get("phone_number_id"):
            raise IntegrationError("Save the access token and the Phone number ID first.")
        r = self._post(
            self._url("/messages"),
            headers={"Authorization": f"Bearer {self.secret}"},
            json={"messaging_product": "whatsapp", "to": to} | body,
        )
        if not r.ok:
            try:
                detail = r.json().get("error", {}).get("message", "")[:150]
            except ValueError:
                detail = ""
            raise IntegrationError(f"WhatsApp said {r.status_code}. {detail}".strip())
        return r.json().get("messages", [{}])[0].get("id", "")


class ViberAdapter(MessageAdapter):
    """Viber bot API (only reaches users who subscribed to the bot)."""

    provider, label = "viber", "Viber (bot)"
    secret_label = "Bot token"
    extra_fields = [("sender_name", "Sender name", "CyberQuest")]
    help_text = "Create a Viber bot (partners.viber.com). Viber sends only to users who subscribed to the bot."

    def test_connection(self):
        def run():
            r = self._post("https://chatapi.viber.com/pa/get_account_info", headers={"X-Viber-Auth-Token": self.secret})
            ok = r.ok and r.json().get("status") == 0
            return (True, "Connected to Viber.") if ok else (False, "Viber did not accept the token.")

        return self._safe_test(run)

    def send(self, to, text):
        r = self._post(
            "https://chatapi.viber.com/pa/send_message",
            headers={"X-Viber-Auth-Token": self.secret},
            json={"receiver": to, "type": "text", "sender": {"name": self.extra["sender_name"]}, "text": text[:7000]},
        )
        if not r.ok or r.json().get("status") != 0:
            raise IntegrationError("Viber could not send the message.")
        return str(r.json().get("message_token", ""))


# --------------------------------------------------------------------- share
class ShareLinks(Adapter):
    """Free share links – no key, no account (WhatsApp, Viber, Facebook)."""

    provider, label, kind, needs_secret = "share", "Share links (free)", "share", False
    extra_fields = [("facebook_page", "School / company Facebook page link", "")]
    help_text = (
        "Free buttons that open WhatsApp, Viber or Facebook with a ready message. Nothing is sent automatically."
    )

    def test_connection(self):
        return True, "Share links work without a key."

    @staticmethod
    def whatsapp(text: str) -> str:
        return f"https://wa.me/?text={quote(text)}"

    @staticmethod
    def viber(text: str) -> str:
        return f"viber://forward?text={quote(text)}"

    @staticmethod
    def facebook(url: str) -> str:
        return f"https://www.facebook.com/sharer/sharer.php?u={quote(url, safe='')}"


ADAPTERS: dict[str, type[Adapter]] = {
    cls.provider: cls
    for cls in (
        OfflineTemplateProvider,
        GeminiProvider,
        DeepSeekProvider,
        ClaudeProvider,
        OpenAIProvider,
        CustomAIProvider,
        GmailAdapter,
        GoogleMapsAdapter,
        WhatsAppAdapter,
        ViberAdapter,
        ShareLinks,
    )
}
# Default order when no default is chosen (agreed with the Product Owner): Gemini first, then DeepSeek.
AI_ORDER = ["gemini", "deepseek", "claude", "openai", "custom_ai"]

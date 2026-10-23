"""
adapters.py - One class per outside service (Adapter pattern)
=============================================================

Owner: Jihe Qi (task J-10)

Every service looks different on the outside (OpenAI, Claude, Gemini, Gmail,
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
class AIProvider(Adapter):
    """Parent for AI text generators."""

    kind = "ai"

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 400) -> str:
        """Return generated text."""


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


class OpenAIProvider(AIProvider):
    """OpenAI chat completions."""

    provider, label = "openai", "OpenAI"
    extra_fields = [("model", "Model", "gpt-4o-mini"), ("base_url", "API address", "https://api.openai.com/v1")]
    help_text = "Create a key at platform.openai.com → API keys. Usage is charged by OpenAI."

    def _headers(self):
        return {"Authorization": f"Bearer {self.secret}", "Content-Type": "application/json"}

    def test_connection(self):
        def run():
            r = self._get(f"{self.extra['base_url']}/models", headers=self._headers())
            return (True, "Connected to OpenAI.") if r.ok else (False, f"OpenAI said {r.status_code}.")

        return self._safe_test(run)

    def generate(self, prompt, max_tokens=400):
        r = self._post(
            f"{self.extra['base_url']}/chat/completions",
            headers=self._headers(),
            json={
                "model": self.extra["model"],
                "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            },
        )
        if not r.ok:
            raise IntegrationError(f"OpenAI said {r.status_code}.")
        return r.json()["choices"][0]["message"]["content"].strip()


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

    def test_connection(self):
        def run():
            r = self._get(f"{self.extra['base_url']}/models", headers=self._headers())
            return (True, "Connected to Claude.") if r.ok else (False, f"Anthropic said {r.status_code}.")

        return self._safe_test(run)

    def generate(self, prompt, max_tokens=400):
        r = self._post(
            f"{self.extra['base_url']}/messages",
            headers=self._headers(),
            json={
                "model": self.extra["model"],
                "max_tokens": max_tokens,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        if not r.ok:
            raise IntegrationError(f"Anthropic said {r.status_code}.")
        return "".join(part.get("text", "") for part in r.json().get("content", [])).strip()


class GeminiProvider(AIProvider):
    """Google Gemini generateContent API."""

    provider, label = "gemini", "Google Gemini"
    extra_fields = [
        ("model", "Model", "gemini-2.5-flash"),
        ("base_url", "API address", "https://generativelanguage.googleapis.com/v1beta"),
    ]
    help_text = "Create a key at aistudio.google.com → Get API key."

    def test_connection(self):
        def run():
            r = self._get(f"{self.extra['base_url']}/models", params={"key": self.secret})
            return (True, "Connected to Gemini.") if r.ok else (False, f"Google said {r.status_code}.")

        return self._safe_test(run)

    def generate(self, prompt, max_tokens=400):
        r = self._post(
            f"{self.extra['base_url']}/models/{self.extra['model']}:generateContent",
            params={"key": self.secret},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens},
            },
        )
        if not r.ok:
            raise IntegrationError(f"Google said {r.status_code}.")
        parts = r.json()["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()


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
    extra_fields = [("phone_number_id", "Phone number ID", ""), ("api_version", "Graph API version", "v20.0")]
    help_text = (
        "Needs a Meta business account and WhatsApp Business Platform. Business-started messages need "
        "approved templates and are charged per message. Parents must opt in."
    )

    def _url(self, path=""):
        return f"https://graph.facebook.com/{self.extra['api_version']}/{self.extra['phone_number_id']}{path}"

    def test_connection(self):
        def run():
            r = self._get(self._url(), headers={"Authorization": f"Bearer {self.secret}"})
            return (True, "Connected to WhatsApp.") if r.ok else (False, f"Meta said {r.status_code}.")

        return self._safe_test(run)

    def send(self, to, text):
        r = self._post(
            self._url("/messages"),
            headers={"Authorization": f"Bearer {self.secret}"},
            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000]}},
        )
        if not r.ok:
            raise IntegrationError(f"WhatsApp said {r.status_code}.")
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
        ClaudeProvider,
        OpenAIProvider,
        GeminiProvider,
        GmailAdapter,
        GoogleMapsAdapter,
        WhatsAppAdapter,
        ViberAdapter,
        ShareLinks,
    )
}
AI_ORDER = ["claude", "openai", "gemini"]

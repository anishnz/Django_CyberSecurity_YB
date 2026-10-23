"""
youtube.py - Turn a YouTube link into a safe embed link
=======================================================

Owner: Jihe Qi (task J-12)

Only real YouTube links are accepted. The embed uses youtube-nocookie.com
(privacy-enhanced mode), which the Content Security Policy allows in iframes.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from apps.core.exceptions import ValidationError

ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtube-nocookie.com"}


def video_id(url: str) -> str:
    """Return the 11-character video id, or raise ValidationError."""
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in ("http", "https") or parsed.netloc.lower() not in HOSTS:
        raise ValidationError("Please paste a YouTube link (youtube.com or youtu.be).")
    if parsed.netloc.lower() == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif parsed.path.startswith(("/embed/", "/shorts/", "/live/")):
        candidate = parsed.path.split("/")[2]
    else:
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    if not ID_RE.match(candidate or ""):
        raise ValidationError("We could not find the video id in that YouTube link.")
    return candidate


def embed_url(url: str) -> str:
    """https://www.youtube-nocookie.com/embed/<id>"""
    return f"https://www.youtube-nocookie.com/embed/{video_id(url)}"


def safe_embed_url(url: str) -> str:
    """Like embed_url but returns '' instead of raising (for templates)."""
    try:
        return embed_url(url) if url else ""
    except ValidationError:
        return ""

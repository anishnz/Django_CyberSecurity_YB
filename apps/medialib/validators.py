"""
validators.py - Safe file uploads (type by file signature + size limit)
=======================================================================

Owner: Jihe Qi (task J-12). Used by the media library, ticket attachments and payslips.

* The file's first bytes (its "signature") must match an allowed type – a
  renamed .exe called photo.jpg is rejected even though its name looks safe.
* The size must be under the limit set by the Super Admin (SystemSettings).
* Rejected uploads are written to the security log.
"""

from __future__ import annotations

import filetype

from apps.core.exceptions import UploadRejectedError
from apps.core.models import SystemSettings

ALLOWED = {
    "image": {"image/jpeg", "image/png", "image/webp", "image/gif"},
    "audio": {"audio/mpeg", "audio/ogg", "audio/x-wav", "audio/wav", "audio/mp4", "audio/m4a", "audio/x-m4a"},
    "video": {"video/mp4", "video/webm", "video/quicktime"},
    "document": {"application/pdf"},
}
ALLOWED["payslip"] = ALLOWED["image"] | ALLOWED["document"]
ALLOWED["attachment"] = ALLOWED["image"] | ALLOWED["document"]
LIMIT_KIND = {"payslip": "document", "attachment": "document"}


def check_upload(uploaded, kind: str, request=None, user=None) -> str:
    """Return the real MIME type, or raise UploadRejectedError with a friendly message."""
    cfg = SystemSettings.load()
    limit = cfg.max_bytes(LIMIT_KIND.get(kind, kind))
    if uploaded.size > limit:
        _log(request, user, f"{uploaded.name}: too big ({uploaded.size} bytes)")
        raise UploadRejectedError(f"This file is too big. The limit is {limit // (1024 * 1024)} MB.")
    head = uploaded.read(8192)
    uploaded.seek(0)
    guess = filetype.guess(head)
    mime = guess.mime if guess else ""
    if mime not in ALLOWED[kind]:
        _log(request, user, f"{uploaded.name}: type '{mime or 'unknown'}' not allowed for {kind}")
        nice = {
            "image": "JPG, PNG, WebP or GIF",
            "audio": "MP3, OGG, WAV or M4A",
            "video": "MP4 or WebM",
            "document": "PDF",
            "payslip": "PDF, JPG or PNG",
            "attachment": "PDF, JPG or PNG",
        }[kind]
        raise UploadRejectedError(f"This file type is not allowed. Please upload {nice}.")
    return mime


def _log(request, user, details: str) -> None:
    from apps.security.services import SecurityLog  # pylint: disable=import-outside-toplevel

    SecurityLog.record("upload_rejected", request, user or getattr(request, "user", None), details=details)

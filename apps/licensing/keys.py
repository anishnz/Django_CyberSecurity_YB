"""
keys.py - Offline product keys and Level Pack keys (HMAC check code)
====================================================================

Owner: Rajneesh Kumar (task R-06)

Key format:  CQ-BRIGHTSTAR-BASIC-20271231-7F3A   (product key)
             CQ-BRIGHTSTAR-L4-20271231-9B1C      (Level Pack key)
The last 4 characters are the first 4 hex characters of
HMAC-SHA256(secret, "CQ-SCHOOL-KIND-DATE"). Editing any part breaks the check.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import date

from django.conf import settings

from apps.core.exceptions import InvalidLicenseKeyError

from .plans import PLAN_CLASSES, UNLIMITED_EXPIRY

KEY_PATTERN = re.compile(
    r"^CQ-(?P<school>[A-Z0-9]{3,20})-(?P<kind>TRIAL|BASIC|STANDARD|UNLIMITED|L[2-6])-"
    r"(?P<date>\d{8})-(?P<check>[0-9A-F]{4})$"
)


@dataclass(frozen=True)
class KeyInfo:
    """The parts of a valid key (frozen = cannot be changed after it is made)."""

    key: str
    school_code: str
    plan: str | None
    level: int | None
    expiry: date

    @property
    def is_level_pack(self) -> bool:
        return self.level is not None


class LicenseKeyValidator:
    """Creates and checks keys using a shared secret."""

    def __init__(self, secret: str | None = None):
        secret = secret or settings.LICENSE_SECRET
        if not secret:
            raise ValueError("A secret is needed to create or check keys.")
        self._secret = secret.encode()

    def check_code(self, school: str, kind: str, date_text: str) -> str:
        message = f"CQ-{school}-{kind}-{date_text}".encode()
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()[:4].upper()

    def generate(self, school_code: str, kind: str, expiry: date | None) -> str:
        """Make a key, e.g. generate('BRIGHTSTAR', 'BASIC', date(2027, 12, 31)) or (…, 'L4', …)."""
        kind = kind.upper()
        if kind not in PLAN_CLASSES and not re.fullmatch(r"L[2-6]", kind):
            raise InvalidLicenseKeyError(f"Unknown plan or Level Pack '{kind}'.")
        if kind == "UNLIMITED" or expiry is None:
            expiry = UNLIMITED_EXPIRY
        date_text = expiry.strftime("%Y%m%d")
        school_code = school_code.upper()
        return f"CQ-{school_code}-{kind}-{date_text}-{self.check_code(school_code, kind, date_text)}"

    def parse(self, key: str) -> KeyInfo:
        """Check the format and check code; return the parts."""
        cleaned = (key or "").strip().upper()
        match = KEY_PATTERN.match(cleaned)
        if not match:
            raise InvalidLicenseKeyError("Invalid key format. A key looks like CQ-SCHOOLCODE-BASIC-20271231-ABCD.")
        school, kind, date_text, check = match.group("school", "kind", "date", "check")
        if not hmac.compare_digest(self.check_code(school, kind, date_text), check):
            raise InvalidLicenseKeyError(
                "This key is not valid: the check code does not match. It may have been typed wrongly or edited."
            )
        try:
            expiry = date(int(date_text[:4]), int(date_text[4:6]), int(date_text[6:]))
        except ValueError as exc:
            raise InvalidLicenseKeyError("This key is not valid: the date is not a real date.") from exc
        if kind.startswith("L"):
            return KeyInfo(cleaned, school, None, int(kind[1]), expiry)
        return KeyInfo(cleaned, school, kind, None, expiry)

    def validate_for_school(self, key: str, school_code: str, today: date, level_pack: bool = False) -> KeyInfo:
        """Right school, right kind of key, not already expired."""
        info = self.parse(key)
        if info.school_code != school_code.upper():
            raise InvalidLicenseKeyError("This key belongs to another school.")
        if level_pack and not info.is_level_pack:
            raise InvalidLicenseKeyError("This is a product key, not a Level Pack key.")
        if not level_pack and info.is_level_pack:
            raise InvalidLicenseKeyError("This is a Level Pack key. Enter it in the Level Pack box.")
        if info.expiry < today:
            raise InvalidLicenseKeyError("This key has already expired.")
        return info

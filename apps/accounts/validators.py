"""validators.py - Password and name rules. Owner: Anish Shrestha."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

NAME_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿĀ-ſ' \-]{1,60}$")


class LetterAndNumberValidator:
    """A password must have at least one letter and one number."""

    def validate(self, password, user=None):  # pylint: disable=unused-argument
        """Raise ValidationError if a letter or a number is missing."""
        if not re.search(r"[A-Za-z]", password or "") or not re.search(r"\d", password or ""):
            raise ValidationError("Password must contain at least one letter and one number.",
                                  code="password_letter_number")

    def get_help_text(self):
        """Text shown under password fields."""
        return "Use at least one letter and one number."


def validate_person_name(value: str) -> str:
    """Names may use letters (including macrons like ā), spaces, hyphens and apostrophes."""
    value = (value or "").strip()
    if not NAME_RE.match(value):
        raise ValidationError("Names can only use letters (including macrons), spaces, hyphens and apostrophes.")
    return value

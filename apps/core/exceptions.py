"""
exceptions.py - CyberQuest's own error classes
==============================================

Owner: Anish Shrestha (task A-18)

Concepts:
    * Inheritance: every error is a child of CyberQuestError, so one handler
      (core.middleware.FriendlyErrorMiddleware) can catch them all.
    * Each class carries a friendly ``message`` and an HTTP ``status``. Pages never
      show raw Python errors to users (NFR-02).
"""

from __future__ import annotations


class CyberQuestError(Exception):
    """Base class for expected problems the user can understand and fix."""

    status = 400
    default_message = "Something is not right. Please check and try again."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationError(CyberQuestError):
    """Form or data is not valid (empty name, wrong date, ...)."""

    default_message = "Please check the information and try again."


class AccessDeniedError(CyberQuestError):
    """The user's role or school does not allow this action."""

    status = 403
    default_message = "Sorry, you don't have access to this page."


class NotFoundError(CyberQuestError):
    """The item does not exist (or is not in the user's school)."""

    status = 404
    default_message = "We couldn't find that."


class SectionFullError(CyberQuestError):
    """A section already has its maximum number of students (default 35)."""

    default_message = "This section is full. Ask the Super Admin to raise the limit."


class LicenseExpiredError(CyberQuestError):
    """The school's licence has ended (after the grace period)."""

    status = 403
    default_message = "Your school's CyberQuest licence has ended. Please ask your School Admin to renew it."


class LicenseLimitError(CyberQuestError):
    """The plan does not allow more sections."""

    default_message = "Your plan does not allow more sections. Ask about upgrading your plan."


class InvalidLicenseKeyError(CyberQuestError):
    """A product key or Level Pack key is wrong, edited or for another school."""

    default_message = "This key is not valid. Please check each part."


class LevelLockedError(CyberQuestError):
    """The student cannot open this level yet."""

    status = 403
    default_message = "This level is locked. Ask your teacher about this level."


class ConfirmationRequiredError(CyberQuestError):
    """A dangerous action needs a typed confirmation word."""

    default_message = "Please type the confirmation word exactly."


class ReadOnlyError(CyberQuestError):
    """Demo Guest (or maintenance mode) cannot change data."""

    status = 403
    default_message = "Demo Guest is read-only. Nothing can be changed."


class UploadRejectedError(CyberQuestError):
    """An uploaded file is the wrong type or too big."""

    default_message = "This file cannot be uploaded. Check the file type and size."


class IntegrationError(CyberQuestError):
    """An outside service (AI, email, WhatsApp ...) failed or is not set up."""

    status = 502
    default_message = "The outside service did not answer. Please check its settings."

"""
Data validation utilities for contacts and leads.

Validates email addresses, phone numbers, and other fields
before they are sent to external services.
"""

import re
from typing import Optional

# RFC 5322 simplified email regex
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
    r"[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)

# Known disposable email domains (small sample — extend as needed)
_DISPOSABLE_DOMAINS = frozenset({
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "sharklasers.com", "guerrillamailblock.com", "grr.la",
    "dispostable.com", "trashmail.com",
})


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    Returns True if the email has valid syntax and is not a disposable domain.
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        return False

    domain = email.rsplit("@", 1)[1]
    if domain in _DISPOSABLE_DOMAINS:
        return False

    return True


def validate_phone(phone: str) -> bool:
    """
    Validate a phone number (US format).
    Accepts 10-11 digit numbers after stripping non-digits.
    """
    if not phone:
        return False

    digits = re.sub(r"\D", "", str(phone))
    return len(digits) in (10, 11)


def validate_url(url: str) -> bool:
    """Validate a URL has proper format."""
    if not url:
        return False
    return bool(re.match(r"^https?://[^\s/$.?#].[^\s]*$", url, re.IGNORECASE))


def validate_lead_score(score: float) -> bool:
    """Validate a lead score is within range."""
    return isinstance(score, (int, float)) and 0 <= score <= 100

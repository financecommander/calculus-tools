"""
Data normalization utilities for contacts and leads.

Provides consistent formatting for email addresses, phone numbers, and names.
"""

import re
from typing import Optional


def normalize_email(email: str) -> str:
    """
    Normalize an email address.
    - Lowercase
    - Strip whitespace
    - Remove dots from Gmail local part (user.name@gmail.com -> username@gmail.com)
    - Remove plus-addressing (user+tag@domain -> user@domain)
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        return email

    local, domain = email.rsplit("@", 1)

    # Remove plus-addressing
    if "+" in local:
        local = local.split("+")[0]

    # Gmail dot normalization
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")

    return f"{local}@{domain}"


def normalize_phone(phone: str) -> str:
    """
    Normalize a US phone number to E.164 format (+1XXXXXXXXXX).
    Strips all non-digit characters, prepends +1 if 10 digits.
    """
    if not phone:
        return ""

    digits = re.sub(r"\D", "", str(phone))

    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) > 11:
        return f"+{digits}"

    return digits


def normalize_name(name: str) -> str:
    """
    Normalize a person's name.
    - Strip whitespace
    - Title case
    - Collapse multiple spaces
    """
    if not name:
        return ""
    name = re.sub(r"\s+", " ", name.strip())
    return name.title()


def split_name(full_name: str) -> tuple:
    """
    Split a full name into (first_name, last_name).
    Returns ("", "") for empty input.
    """
    if not full_name:
        return ("", "")

    parts = full_name.strip().split()
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        return (parts[0], " ".join(parts[1:]))

"""
Contact deduplication utilities.

Deduplicates contacts by normalized email, phone, or composite key
before sending to external services.
"""

from typing import Dict, List, Any, Optional, Set
from calculus_tools.utils.normalizers import normalize_email, normalize_phone


def dedupe_contacts(
    contacts: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Remove duplicate contacts based on normalized key fields.

    Args:
        contacts: List of contact dicts
        key_fields: Fields to use for dedup key. Defaults to ["email"].

    Returns:
        Deduplicated list preserving first occurrence order.
    """
    if key_fields is None:
        key_fields = ["email"]

    seen: Set[str] = set()
    unique: List[Dict[str, Any]] = []

    for contact in contacts:
        key_parts = []
        for field in key_fields:
            value = contact.get(field, "")
            if field == "email" and value:
                value = normalize_email(value)
            elif field == "phone" and value:
                value = normalize_phone(value)
            key_parts.append(str(value).strip().lower())

        composite_key = "|".join(key_parts)
        if composite_key and composite_key not in seen:
            seen.add(composite_key)
            unique.append(contact)

    return unique


def find_duplicates(
    contacts: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None,
) -> Dict[str, List[int]]:
    """
    Find duplicate groups by key fields.

    Returns:
        Dict mapping composite key to list of indices in the original list.
    """
    if key_fields is None:
        key_fields = ["email"]

    groups: Dict[str, List[int]] = {}

    for idx, contact in enumerate(contacts):
        key_parts = []
        for field in key_fields:
            value = contact.get(field, "")
            if field == "email" and value:
                value = normalize_email(value)
            elif field == "phone" and value:
                value = normalize_phone(value)
            key_parts.append(str(value).strip().lower())

        composite_key = "|".join(key_parts)
        if composite_key:
            groups.setdefault(composite_key, []).append(idx)

    return {k: v for k, v in groups.items() if len(v) > 1}

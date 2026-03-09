"""
Shared utilities for data processing, validation, and rate limiting.
"""

from calculus_tools.utils.dedupe import dedupe_contacts
from calculus_tools.utils.normalizers import normalize_email, normalize_phone, normalize_name
from calculus_tools.utils.validators import validate_email, validate_phone
from calculus_tools.utils.rate_limiter import RateLimiter

__all__ = [
    "dedupe_contacts",
    "normalize_email",
    "normalize_phone",
    "normalize_name",
    "validate_email",
    "validate_phone",
    "RateLimiter",
]

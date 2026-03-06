"""Pydantic models for the API Registry."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class ApiCategory(str, Enum):
    TESTING = "testing"
    API_DISCOVERY = "api_discovery"
    FUN = "fun"
    DEMOGRAPHICS = "demographics"
    NETWORK = "network"
    GEOLOCATION = "geolocation"
    FINANCE = "finance"
    CALENDAR = "calendar"
    NEWS = "news"
    MARKET_DATA = "market_data"
    SEC = "sec"
    SOCIAL = "social"
    LEGAL = "legal"
    CORPORATE = "corporate"
    CHEMISTRY = "chemistry"
    NUTRITION = "nutrition"
    KNOWLEDGE = "knowledge"
    OTHER = "other"


class ApiEntry(BaseModel):
    """Single API in the registry."""

    api_id: Optional[int] = Field(None, description="Auto-assigned DB primary key")
    name: str = Field(..., max_length=120)
    base_url: str = Field(..., description="Base URL or example endpoint")
    auth_type: AuthType = AuthType.NONE
    rate_limit: Optional[str] = Field(None, max_length=100, description="e.g. '45 req/min'")
    cost_per_call: float = Field(0.0, ge=0.0, description="USD cost per request")
    category: ApiCategory = ApiCategory.OTHER
    notes: str = Field("", max_length=500)
    enabled: bool = True

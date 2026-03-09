"""
Data Enrichment Client — Stub for MVP.

Planned capabilities:
- Contact enrichment (email, phone, title, company from name/domain)
- Company enrichment (revenue, employee count, industry)
- Social profile discovery
"""

from typing import Dict, Any, Optional


class EnrichmentClient:
    """Data enrichment client (stub — not yet implemented)."""

    def __init__(self, provider: str = "clearbit", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key

    async def enrich_contact(self, email: Optional[str] = None, name: Optional[str] = None,
                              domain: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("Contact enrichment not yet implemented")

    async def enrich_company(self, domain: str) -> Dict[str, Any]:
        raise NotImplementedError("Company enrichment not yet implemented")

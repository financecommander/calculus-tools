"""HubSpot client — contacts, deals, and companies via HubSpot CRM API v3."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.hubapi.com"


class HubSpotClient:
    """Async HubSpot CRM API client.

    Usage::

        async with HubSpotClient(api_key="pat-...") as hs:
            contact = await hs.create_contact(
                email="lead@example.com",
                properties={"firstname": "Jane", "lastname": "Doe"},
            )
    """

    def __init__(self, api_key: str, *, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    # ── Contacts ──────────────────────────────────────────────────

    async def create_contact(self, email: str, properties: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a CRM contact."""
        props = {"email": email, **(properties or {})}
        resp = await self._client.post("/crm/v3/objects/contacts", json={"properties": props})
        resp.raise_for_status()
        return resp.json()

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get a contact by ID."""
        resp = await self._client.get(f"/crm/v3/objects/contacts/{contact_id}")
        resp.raise_for_status()
        return resp.json()

    async def search_contacts(self, query: str, *, limit: int = 10) -> Dict[str, Any]:
        """Search contacts by email, name, etc."""
        payload = {
            "filterGroups": [{"filters": [{"propertyName": "email", "operator": "CONTAINS_TOKEN", "value": query}]}],
            "limit": limit,
        }
        resp = await self._client.post("/crm/v3/objects/contacts/search", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_contact(self, contact_id: str, properties: Dict[str, str]) -> Dict[str, Any]:
        """Update a contact's properties."""
        resp = await self._client.patch(f"/crm/v3/objects/contacts/{contact_id}", json={"properties": properties})
        resp.raise_for_status()
        return resp.json()

    # ── Deals ─────────────────────────────────────────────────────

    async def create_deal(self, name: str, stage: str = "appointmentscheduled",
                          properties: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a deal."""
        props = {"dealname": name, "dealstage": stage, **(properties or {})}
        resp = await self._client.post("/crm/v3/objects/deals", json={"properties": props})
        resp.raise_for_status()
        return resp.json()

    async def list_deals(self, *, limit: int = 20) -> Dict[str, Any]:
        """List deals."""
        resp = await self._client.get("/crm/v3/objects/deals", params={"limit": limit})
        resp.raise_for_status()
        return resp.json()

    # ── Companies ─────────────────────────────────────────────────

    async def create_company(self, name: str, domain: str = "",
                              properties: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a company."""
        props = {"name": name, **(properties or {})}
        if domain:
            props["domain"] = domain
        resp = await self._client.post("/crm/v3/objects/companies", json={"properties": props})
        resp.raise_for_status()
        return resp.json()

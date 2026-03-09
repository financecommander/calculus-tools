"""HubSpot CRM API v3 client for contacts, deals, companies, and notes.

Usage::

    client = HubSpotClient(access_token="pat-na1-...")
    contact = await client.create_contact("alice@example.com", first_name="Alice")
    deal = await client.create_deal("Big Deal", "default", "appointmentscheduled", amount=10000)
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.hubapi.com"


class HubSpotClient:
    """Async HubSpot CRM API v3 client."""

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def create_contact(
        self, email: str, *, first_name: str = "", last_name: str = "", **extra: str
    ) -> dict[str, Any]:
        """Create a new CRM contact."""
        properties = {"email": email, "firstname": first_name, "lastname": last_name, **extra}
        logger.info("Creating contact %s", email)
        resp = await self._client.post(
            "/crm/v3/objects/contacts", json={"properties": properties}
        )
        resp.raise_for_status()
        return resp.json()

    async def update_contact(
        self, contact_id: str, properties: dict[str, str]
    ) -> dict[str, Any]:
        """Update an existing contact by ID."""
        logger.info("Updating contact %s", contact_id)
        resp = await self._client.patch(
            f"/crm/v3/objects/contacts/{contact_id}",
            json={"properties": properties},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Retrieve a contact by ID."""
        logger.debug("Fetching contact %s", contact_id)
        resp = await self._client.get(f"/crm/v3/objects/contacts/{contact_id}")
        resp.raise_for_status()
        return resp.json()

    async def search_contacts(
        self, query: str, *, limit: int = 10
    ) -> dict[str, Any]:
        """Full-text search for contacts."""
        logger.debug("Searching contacts: %s", query)
        resp = await self._client.post(
            "/crm/v3/objects/contacts/search",
            json={"query": query, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    async def list_contacts(
        self, *, limit: int = 100, after: str | None = None
    ) -> dict[str, Any]:
        """List contacts with cursor-based pagination."""
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if after:
            params["after"] = after
        logger.debug("Listing contacts (limit=%d)", limit)
        resp = await self._client.get("/crm/v3/objects/contacts", params=params)
        resp.raise_for_status()
        return resp.json()

    async def create_deal(
        self,
        deal_name: str,
        pipeline: str,
        deal_stage: str,
        *,
        amount: float | None = None,
        **extra: str,
    ) -> dict[str, Any]:
        """Create a new deal in a pipeline."""
        properties: dict[str, Any] = {
            "dealname": deal_name,
            "pipeline": pipeline,
            "dealstage": deal_stage,
            **extra,
        }
        if amount is not None:
            properties["amount"] = str(amount)
        logger.info("Creating deal '%s' in pipeline %s", deal_name, pipeline)
        resp = await self._client.post(
            "/crm/v3/objects/deals", json={"properties": properties}
        )
        resp.raise_for_status()
        return resp.json()

    async def list_deals(
        self, *, limit: int = 100, after: str | None = None
    ) -> dict[str, Any]:
        """List deals with cursor-based pagination."""
        params: dict[str, Any] = {"limit": min(limit, 100)}
        if after:
            params["after"] = after
        logger.debug("Listing deals (limit=%d)", limit)
        resp = await self._client.get("/crm/v3/objects/deals", params=params)
        resp.raise_for_status()
        return resp.json()

    async def create_company(
        self, name: str, *, domain: str = "", **extra: str
    ) -> dict[str, Any]:
        """Create a new company."""
        properties: dict[str, Any] = {"name": name, "domain": domain, **extra}
        logger.info("Creating company '%s'", name)
        resp = await self._client.post(
            "/crm/v3/objects/companies", json={"properties": properties}
        )
        resp.raise_for_status()
        return resp.json()

    async def search_companies(
        self, query: str, *, limit: int = 10
    ) -> dict[str, Any]:
        """Full-text search for companies."""
        logger.debug("Searching companies: %s", query)
        resp = await self._client.post(
            "/crm/v3/objects/companies/search",
            json={"query": query, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_note(
        self, body: str, *, associations: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Create a note (engagement) optionally associated with CRM objects."""
        payload: dict[str, Any] = {
            "properties": {"hs_note_body": body},
        }
        if associations:
            payload["associations"] = associations
        logger.info("Creating note")
        resp = await self._client.post(
            "/crm/v3/objects/notes", json=payload
        )
        resp.raise_for_status()
        return resp.json()

    async def list_pipelines(
        self, object_type: str = "deals"
    ) -> list[dict[str, Any]]:
        """List pipelines for a given object type (deals or tickets)."""
        logger.debug("Listing %s pipelines", object_type)
        resp = await self._client.get(
            f"/crm/v3/pipelines/{object_type}"
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

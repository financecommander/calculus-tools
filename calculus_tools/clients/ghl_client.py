"""
GoHighLevel (GHL) CRM Client

Full implementation for contact management, workflow triggers, and tag operations
via the GHL v2 API (services.leadconnectorhq.com).

Extracted and expanded from SWARM/workflows/leadgen/auto_sender.py.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import date

import aiohttp

logger = logging.getLogger(__name__)

GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"


@dataclass
class GHLContact:
    """Represents a GHL contact record."""
    first_name: str
    last_name: str = ""
    email: str = ""
    phone: str = ""
    tags: List[str] = field(default_factory=list)
    location_id: str = ""
    custom_fields: Optional[Dict[str, str]] = None
    contact_id: Optional[str] = None


@dataclass
class GHLResult:
    """Result of a GHL API operation."""
    success: bool
    contact_id: str = ""
    status_code: int = 0
    error: str = ""
    data: Optional[Dict[str, Any]] = None


class GHLClient:
    """
    GoHighLevel CRM client with contact CRUD, workflow triggers, and tag management.

    Usage:
        client = GHLClient()  # reads GHL_API_KEY and GHL_LOCATION_ID from env
        result = await client.create_contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            tags=["mortgage-lead", "swarm-generated"]
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        location_id: Optional[str] = None,
        daily_limit: int = 150,
    ):
        self.api_key = api_key or os.getenv("GHL_API_KEY", "")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID", "")
        self.daily_limit = daily_limit
        self._sent_file = os.getenv("GHL_SENT_FILE", "ghl_sent_today.json")

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": GHL_API_VERSION,
        }

    def _get_daily_count(self) -> int:
        """Get number of contacts created today."""
        today = str(date.today())
        try:
            with open(self._sent_file) as f:
                sent = json.load(f)
            return sent.get(today, 0)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return 0

    def _increment_daily_count(self, count: int = 1) -> None:
        """Increment daily send counter."""
        today = str(date.today())
        try:
            with open(self._sent_file) as f:
                sent = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            sent = {}
        sent[today] = sent.get(today, 0) + count
        with open(self._sent_file, "w") as f:
            json.dump(sent, f)

    def _check_daily_limit(self) -> bool:
        """Check if daily limit has been reached."""
        return self._get_daily_count() < self.daily_limit

    async def create_contact(
        self,
        first_name: str,
        last_name: str = "",
        email: str = "",
        phone: str = "",
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, str]] = None,
        dry_run: bool = False,
    ) -> GHLResult:
        """Create a new contact in GHL."""
        if not self._check_daily_limit():
            return GHLResult(
                success=False,
                error=f"Daily limit of {self.daily_limit} contacts reached",
            )

        payload: Dict[str, Any] = {
            "firstName": first_name,
            "lastName": last_name,
            "locationId": self.location_id,
        }
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if tags:
            payload["tags"] = tags
        if custom_fields:
            payload["customField"] = custom_fields

        if dry_run:
            logger.info("DRY RUN - Would create GHL contact: %s %s <%s>",
                        first_name, last_name, email)
            return GHLResult(success=True, contact_id="dry-run")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{GHL_BASE_URL}/contacts/",
                    json=payload,
                    headers=self._headers,
                ) as resp:
                    if resp.status in (200, 201):
                        data = await resp.json()
                        contact_id = data.get("contact", {}).get("id", "")
                        self._increment_daily_count()
                        logger.info("GHL contact created: %s (%s)", email, contact_id)
                        return GHLResult(
                            success=True,
                            contact_id=contact_id,
                            status_code=resp.status,
                            data=data,
                        )
                    else:
                        text = await resp.text()
                        logger.error("GHL create failed for %s: %s %s",
                                     email, resp.status, text[:200])
                        return GHLResult(
                            success=False,
                            status_code=resp.status,
                            error=text[:200],
                        )
            except Exception as e:
                logger.error("GHL create exception for %s: %s", email, e)
                return GHLResult(success=False, error=str(e))

    async def update_contact(
        self,
        contact_id: str,
        updates: Dict[str, Any],
    ) -> GHLResult:
        """Update an existing GHL contact."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(
                    f"{GHL_BASE_URL}/contacts/{contact_id}",
                    json=updates,
                    headers=self._headers,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return GHLResult(
                            success=True,
                            contact_id=contact_id,
                            status_code=resp.status,
                            data=data,
                        )
                    else:
                        text = await resp.text()
                        return GHLResult(
                            success=False,
                            contact_id=contact_id,
                            status_code=resp.status,
                            error=text[:200],
                        )
            except Exception as e:
                return GHLResult(success=False, error=str(e))

    async def search_contacts(
        self,
        query: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Search contacts by query string."""
        params = {
            "query": query,
            "locationId": self.location_id,
            "limit": str(limit),
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{GHL_BASE_URL}/contacts/",
                    params=params,
                    headers=self._headers,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("contacts", [])
            except Exception as e:
                logger.error("GHL search failed: %s", e)
        return []

    async def add_tag(self, contact_id: str, tag: str) -> GHLResult:
        """Add a tag to a contact."""
        return await self.update_contact(contact_id, {"tags": [tag]})

    async def add_to_workflow(
        self,
        contact_id: str,
        workflow_id: str,
    ) -> GHLResult:
        """Add a contact to a GHL workflow/automation."""
        payload = {"contactId": contact_id}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{GHL_BASE_URL}/workflows/{workflow_id}/contacts",
                    json=payload,
                    headers=self._headers,
                ) as resp:
                    if resp.status in (200, 201):
                        return GHLResult(
                            success=True,
                            contact_id=contact_id,
                            status_code=resp.status,
                        )
                    else:
                        text = await resp.text()
                        return GHLResult(
                            success=False,
                            status_code=resp.status,
                            error=text[:200],
                        )
            except Exception as e:
                return GHLResult(success=False, error=str(e))

    async def create_batch(
        self,
        contacts: List[GHLContact],
        dry_run: bool = False,
    ) -> List[GHLResult]:
        """Create multiple contacts in GHL with daily limit enforcement."""
        results = []
        for contact in contacts:
            if not self._check_daily_limit():
                results.append(GHLResult(
                    success=False,
                    error=f"Daily limit of {self.daily_limit} reached",
                ))
                break
            result = await self.create_contact(
                first_name=contact.first_name,
                last_name=contact.last_name,
                email=contact.email,
                phone=contact.phone,
                tags=contact.tags,
                custom_fields=contact.custom_fields,
                dry_run=dry_run,
            )
            results.append(result)
        return results

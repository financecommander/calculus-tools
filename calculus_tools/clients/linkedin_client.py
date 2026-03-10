"""LinkedIn client — posts, profiles, and messaging via LinkedIn Marketing/Community API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.linkedin.com/v2"


class LinkedInClient:
    """Async LinkedIn API client (v2 + Community Management).

    Usage::

        async with LinkedInClient(access_token="AQ...") as li:
            await li.create_post(org_id="urn:li:organization:12345",
                                 text="We just shipped v18.0.0!")
    """

    def __init__(self, access_token: str, *, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json",
                     "X-Restli-Protocol-Version": "2.0.0"},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def get_profile(self) -> Dict[str, Any]:
        """Get the authenticated user's profile."""
        resp = await self._client.get("/userinfo")
        resp.raise_for_status()
        return resp.json()

    async def create_post(self, org_id: str, text: str, *, visibility: str = "PUBLIC") -> Dict[str, Any]:
        """Create a text post on behalf of an organization or person."""
        payload = {
            "author": org_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                },
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": visibility},
        }
        resp = await self._client.post("/ugcPosts", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_organization(self, org_id: str) -> Dict[str, Any]:
        """Get organization details."""
        resp = await self._client.get(f"/organizations/{org_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_follower_count(self, org_id: str) -> Dict[str, Any]:
        """Get follower statistics for an organization."""
        resp = await self._client.get(
            "/organizationalEntityFollowerStatistics",
            params={"q": "organizationalEntity", "organizationalEntity": f"urn:li:organization:{org_id}"},
        )
        resp.raise_for_status()
        return resp.json()

    async def search_people(self, keywords: str, *, count: int = 10) -> Dict[str, Any]:
        """Search for people (requires appropriate API access)."""
        resp = await self._client.get("/search/people", params={"keywords": keywords, "count": count})
        resp.raise_for_status()
        return resp.json()

    async def send_message(self, recipient_urn: str, subject: str, body: str) -> Dict[str, Any]:
        """Send a direct message (requires Messaging API access)."""
        payload = {
            "recipients": [{"person": {"com.linkedin.voyager.messaging.MessagingMember": recipient_urn}}],
            "subject": subject,
            "body": {"com.linkedin.voyager.messaging.MessageBody": {"text": body}},
        }
        resp = await self._client.post("/messages", json=payload)
        resp.raise_for_status()
        return resp.json()

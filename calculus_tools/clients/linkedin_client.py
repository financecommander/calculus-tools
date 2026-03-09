"""LinkedIn API v2 client for profiles, posts, and messaging.

Usage::

    client = LinkedInClient(access_token="AQV...", organization_id="12345")
    profile = await client.get_profile()
    await client.publish_post("Excited to share our latest update!")
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.linkedin.com/v2"


class LinkedInClient:
    """Async LinkedIn API v2 client."""

    def __init__(
        self, access_token: str, *, organization_id: str | None = None
    ) -> None:
        self.access_token = access_token
        self.organization_id = organization_id
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_profile(self) -> dict[str, Any]:
        """Get the authenticated user's profile via OpenID userinfo."""
        logger.debug("Fetching authenticated user profile")
        resp = await self._client.get("https://api.linkedin.com/v2/userinfo")
        resp.raise_for_status()
        return resp.json()

    async def lookup_profile(self, vanity_name: str) -> dict[str, Any]:
        """Look up a member profile by vanity name (public identifier)."""
        logger.debug("Looking up profile: %s", vanity_name)
        resp = await self._client.get(
            "/people", params={"q": "vanityName", "vanityName": vanity_name}
        )
        resp.raise_for_status()
        return resp.json()

    async def publish_post(
        self,
        text: str,
        *,
        author: str | None = None,
        visibility: str = "PUBLIC",
    ) -> dict[str, Any]:
        """Publish a text post (UGC Post). Author defaults to authenticated user.

        If organization_id is set and no author is provided, posts as the org.
        """
        if author is None:
            if self.organization_id:
                author = f"urn:li:organization:{self.organization_id}"
            else:
                profile = await self.get_profile()
                author = f"urn:li:person:{profile['sub']}"
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
        }
        logger.info("Publishing post as %s", author)
        resp = await self._client.post("/ugcPosts", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def send_message(
        self, recipient_urn: str, subject: str, body: str
    ) -> dict[str, Any]:
        """Send a direct message to a LinkedIn member."""
        profile = await self.get_profile()
        sender_urn = f"urn:li:person:{profile['sub']}"
        payload = {
            "recipients": [recipient_urn],
            "subject": subject,
            "body": body,
            "messageType": "MEMBER_TO_MEMBER",
            "attachments": [],
        }
        logger.info("Sending message to %s", recipient_urn)
        resp = await self._client.post(
            "/messages",
            json=payload,
            params={"action": "create"},
            headers={"x-li-format": "json", "sender": sender_urn},
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {"status": resp.status_code}

    async def get_company_page(
        self, organization_id: str | None = None
    ) -> dict[str, Any]:
        """Retrieve an organization page by ID."""
        org_id = organization_id or self.organization_id
        if not org_id:
            raise ValueError("organization_id is required")
        logger.debug("Fetching organization %s", org_id)
        resp = await self._client.get(f"/organizations/{org_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_share_statistics(
        self, share_urn: str, *, organization_id: str | None = None
    ) -> dict[str, Any]:
        """Get engagement statistics for a share or post."""
        org_id = organization_id or self.organization_id
        params: dict[str, str] = {"q": "organizationalEntity"}
        if org_id:
            params["organizationalEntity"] = f"urn:li:organization:{org_id}"
        params["shares[0]"] = share_urn
        logger.debug("Fetching share statistics for %s", share_urn)
        resp = await self._client.get(
            "/organizationalEntityShareStatistics", params=params
        )
        resp.raise_for_status()
        return resp.json()

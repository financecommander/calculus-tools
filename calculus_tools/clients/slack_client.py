"""Slack Web API client using httpx.

Usage::

    client = SlackClient(bot_token="xoxb-...")
    await client.send_message("#general", "Hello from calculus-tools!")
    await client.send_dm("U12345", "Private hello")
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://slack.com/api"


class SlackClient:
    """Async Slack Web API client."""

    def __init__(
        self,
        bot_token: str,
        signing_secret: str | None = None,
        webhook_url: str | None = None,
    ) -> None:
        self.bot_token = bot_token
        self.signing_secret = signing_secret
        self.webhook_url = webhook_url
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {bot_token}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _post(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = await self._client.post(f"/{method}", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            logger.error("Slack API error on %s: %s", method, data.get("error"))
            raise RuntimeError(f"Slack API error: {data.get('error')}")
        logger.debug("Slack %s succeeded", method)
        return data

    async def _get(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._client.get(f"/{method}", params=params or {})
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            logger.error("Slack API error on %s: %s", method, data.get("error"))
            raise RuntimeError(f"Slack API error: {data.get('error')}")
        return data

    async def send_message(
        self, channel: str, text: str, *, thread_ts: str | None = None
    ) -> dict[str, Any]:
        """Post a message to a channel or thread."""
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        logger.info("Sending message to %s", channel)
        return await self._post("chat.postMessage", payload)

    async def send_dm(self, user_id: str, text: str) -> dict[str, Any]:
        """Open a DM conversation with a user and send a message."""
        logger.info("Opening DM with user %s", user_id)
        conv = await self._post("conversations.open", {"users": user_id})
        channel_id = conv["channel"]["id"]
        return await self.send_message(channel_id, text)

    async def upload_file(
        self,
        channels: str,
        content: bytes,
        filename: str,
        *,
        title: str | None = None,
        initial_comment: str | None = None,
    ) -> dict[str, Any]:
        """Upload a file to one or more channels."""
        logger.info("Uploading file %s to %s", filename, channels)
        data: dict[str, Any] = {"channels": channels, "filename": filename}
        if title:
            data["title"] = title
        if initial_comment:
            data["initial_comment"] = initial_comment
        resp = await self._client.post(
            "/files.upload",
            data=data,
            files={"file": (filename, content)},
        )
        resp.raise_for_status()
        result = resp.json()
        if not result.get("ok"):
            raise RuntimeError(f"Slack upload error: {result.get('error')}")
        return result

    async def list_channels(
        self, *, limit: int = 100, types: str = "public_channel"
    ) -> list[dict[str, Any]]:
        """List workspace channels."""
        logger.debug("Listing channels (limit=%d)", limit)
        data = await self._get(
            "conversations.list", {"limit": limit, "types": types}
        )
        return data.get("channels", [])

    async def add_reaction(
        self, channel: str, timestamp: str, name: str
    ) -> dict[str, Any]:
        """Add an emoji reaction to a message."""
        logger.debug("Adding reaction :%s: to %s/%s", name, channel, timestamp)
        return await self._post(
            "reactions.add",
            {"channel": channel, "timestamp": timestamp, "name": name},
        )

    async def create_channel(
        self, name: str, *, is_private: bool = False
    ) -> dict[str, Any]:
        """Create a new channel."""
        logger.info("Creating channel %s (private=%s)", name, is_private)
        return await self._post(
            "conversations.create",
            {"name": name, "is_private": is_private},
        )

    async def send_webhook(
        self, text: str, *, url: str | None = None
    ) -> int:
        """Send a message via an incoming webhook URL. Returns HTTP status."""
        target = url or self.webhook_url
        if not target:
            raise ValueError("No webhook URL configured or provided")
        logger.info("Sending webhook message")
        resp = await self._client.post(target, json={"text": text})
        resp.raise_for_status()
        return resp.status_code

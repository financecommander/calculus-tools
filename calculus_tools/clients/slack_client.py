"""Slack client — send messages, DMs, and channel notifications via Slack Web API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://slack.com/api"


class SlackClient:
    """Async Slack Web API client.

    Usage::

        async with SlackClient(bot_token="xoxb-...") as slack:
            await slack.send_message("#general", "Hello from swarm!")
            await slack.send_dm("U12345", "Private update")
    """

    def __init__(self, bot_token: str, *, timeout: float = 30.0):
        self._token = bot_token
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={"Authorization": f"Bearer {bot_token}", "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def _post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self._client.post(f"/{method}", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")
        return data

    async def send_message(self, channel: str, text: str, *, blocks: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Post a message to a channel."""
        payload: Dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        return await self._post("chat.postMessage", payload)

    async def send_dm(self, user_id: str, text: str) -> Dict[str, Any]:
        """Open a DM conversation and send a message."""
        conv = await self._post("conversations.open", {"users": user_id})
        channel = conv["channel"]["id"]
        return await self.send_message(channel, text)

    async def send_ephemeral(self, channel: str, user: str, text: str) -> Dict[str, Any]:
        """Send an ephemeral message visible only to one user."""
        return await self._post("chat.postEphemeral", {"channel": channel, "user": user, "text": text})

    async def list_channels(self, *, limit: int = 100) -> List[Dict[str, Any]]:
        """List public channels."""
        data = await self._post("conversations.list", {"types": "public_channel", "limit": limit})
        return data.get("channels", [])

    async def set_topic(self, channel: str, topic: str) -> Dict[str, Any]:
        """Set channel topic."""
        return await self._post("conversations.setTopic", {"channel": channel, "topic": topic})

    async def add_reaction(self, channel: str, timestamp: str, name: str) -> Dict[str, Any]:
        """Add an emoji reaction to a message."""
        return await self._post("reactions.add", {"channel": channel, "timestamp": timestamp, "name": name})

    async def upload_file(self, channels: str, content: str, filename: str, title: str = "") -> Dict[str, Any]:
        """Upload a text snippet to a channel."""
        return await self._post("files.upload", {
            "channels": channels, "content": content,
            "filename": filename, "title": title or filename,
        })

"""Discord client — send messages, embeds, and manage channels via Discord Bot API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://discord.com/api/v10"


class DiscordClient:
    """Async Discord Bot API client.

    Usage::

        async with DiscordClient(bot_token="...") as discord:
            await discord.send_message(channel_id, "Deployment complete!")
    """

    def __init__(self, bot_token: str, *, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def send_message(self, channel_id: str, content: str) -> Dict[str, Any]:
        """Send a text message to a channel."""
        resp = await self._client.post(f"/channels/{channel_id}/messages", json={"content": content})
        resp.raise_for_status()
        return resp.json()

    async def send_embed(self, channel_id: str, embed: Dict[str, Any], content: str = "") -> Dict[str, Any]:
        """Send a rich embed to a channel."""
        payload: Dict[str, Any] = {"embeds": [embed]}
        if content:
            payload["content"] = content
        resp = await self._client.post(f"/channels/{channel_id}/messages", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def create_thread(self, channel_id: str, name: str, message_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a thread in a channel."""
        if message_id:
            resp = await self._client.post(
                f"/channels/{channel_id}/messages/{message_id}/threads",
                json={"name": name},
            )
        else:
            resp = await self._client.post(
                f"/channels/{channel_id}/threads",
                json={"name": name, "type": 11},
            )
        resp.raise_for_status()
        return resp.json()

    async def list_guild_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """List channels in a guild."""
        resp = await self._client.get(f"/guilds/{guild_id}/channels")
        resp.raise_for_status()
        return resp.json()

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """Add a reaction to a message."""
        resp = await self._client.put(f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me")
        resp.raise_for_status()

    async def get_guild_member(self, guild_id: str, user_id: str) -> Dict[str, Any]:
        """Get guild member info."""
        resp = await self._client.get(f"/guilds/{guild_id}/members/{user_id}")
        resp.raise_for_status()
        return resp.json()

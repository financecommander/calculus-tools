"""Discord API v10 client for bots and webhooks.

Usage::

    client = DiscordClient(bot_token="MTk...")
    await client.send_message(channel_id, "Hello from calculus-tools!")
    await client.send_embed(channel_id, title="Status", description="All systems go")
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://discord.com/api/v10"


class DiscordClient:
    """Async Discord REST API v10 client."""

    def __init__(
        self, bot_token: str, *, webhook_url: str | None = None
    ) -> None:
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def send_message(
        self, channel_id: str, content: str, *, tts: bool = False
    ) -> dict[str, Any]:
        """Send a text message to a channel."""
        logger.info("Sending message to channel %s", channel_id)
        resp = await self._client.post(
            f"/channels/{channel_id}/messages",
            json={"content": content, "tts": tts},
        )
        resp.raise_for_status()
        return resp.json()

    async def send_embed(
        self,
        channel_id: str,
        *,
        title: str,
        description: str = "",
        color: int = 0x5865F2,
        fields: list[dict[str, Any]] | None = None,
        footer: str | None = None,
    ) -> dict[str, Any]:
        """Send a rich embed to a channel."""
        embed: dict[str, Any] = {
            "title": title,
            "description": description,
            "color": color,
        }
        if fields:
            embed["fields"] = fields
        if footer:
            embed["footer"] = {"text": footer}
        logger.info("Sending embed '%s' to channel %s", title, channel_id)
        resp = await self._client.post(
            f"/channels/{channel_id}/messages", json={"embeds": [embed]}
        )
        resp.raise_for_status()
        return resp.json()

    async def send_webhook(
        self, content: str, *, url: str | None = None, username: str | None = None
    ) -> int:
        """Send a message via a Discord webhook. Returns HTTP status code."""
        target = url or self.webhook_url
        if not target:
            raise ValueError("No webhook URL configured or provided")
        payload: dict[str, Any] = {"content": content}
        if username:
            payload["username"] = username
        logger.info("Sending webhook message")
        resp = await self._client.post(target, json=payload)
        resp.raise_for_status()
        return resp.status_code

    async def list_channels(self, guild_id: str) -> list[dict[str, Any]]:
        """List all channels in a guild."""
        logger.debug("Listing channels for guild %s", guild_id)
        resp = await self._client.get(f"/guilds/{guild_id}/channels")
        resp.raise_for_status()
        return resp.json()

    async def create_channel(
        self,
        guild_id: str,
        name: str,
        *,
        channel_type: int = 0,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """Create a new guild channel. Type 0 = text, 2 = voice."""
        payload: dict[str, Any] = {"name": name, "type": channel_type}
        if topic:
            payload["topic"] = topic
        logger.info("Creating channel %s in guild %s", name, guild_id)
        resp = await self._client.post(
            f"/guilds/{guild_id}/channels", json=payload
        )
        resp.raise_for_status()
        return resp.json()

    async def add_reaction(
        self, channel_id: str, message_id: str, emoji: str
    ) -> None:
        """Add an emoji reaction to a message. Use URL-encoded emoji."""
        logger.debug("Adding reaction %s to %s/%s", emoji, channel_id, message_id)
        resp = await self._client.put(
            f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        )
        resp.raise_for_status()

    async def get_guild_members(
        self, guild_id: str, *, limit: int = 100, after: str | None = None
    ) -> list[dict[str, Any]]:
        """List members of a guild."""
        params: dict[str, Any] = {"limit": min(limit, 1000)}
        if after:
            params["after"] = after
        logger.debug("Listing members for guild %s (limit=%d)", guild_id, limit)
        resp = await self._client.get(
            f"/guilds/{guild_id}/members", params=params
        )
        resp.raise_for_status()
        return resp.json()

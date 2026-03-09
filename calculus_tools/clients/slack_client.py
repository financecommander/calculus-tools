"""
Slack API Client — Stub for MVP.

Planned capabilities:
- Channel and DM messaging with Block Kit support
- File uploads to channels
- Channel management (list, create)
- Emoji reactions
- Thread replies
"""

from typing import Dict, Any, Optional, List


class SlackClient:
    """Slack API client (stub — not yet implemented)."""

    def __init__(self, bot_token: str, signing_secret: Optional[str] = None):
        self.bot_token = bot_token
        self.signing_secret = signing_secret

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Slack send_message not yet implemented")

    async def send_dm(
        self,
        user_id: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Slack send_dm not yet implemented")

    async def upload_file(
        self,
        channels: str,
        file_path: str,
        title: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Slack upload_file not yet implemented")

    async def list_channels(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Slack list_channels not yet implemented")

    async def add_reaction(
        self, channel: str, timestamp: str, emoji: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Slack add_reaction not yet implemented")

    async def create_channel(
        self, name: str, is_private: bool = False
    ) -> Dict[str, Any]:
        raise NotImplementedError("Slack create_channel not yet implemented")

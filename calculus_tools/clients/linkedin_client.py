"""
LinkedIn API Client — Stub for MVP.

Planned capabilities:
- Post publishing (text, image, article)
- Profile lookup and enrichment
- Connection messaging
"""

from typing import Dict, Any, Optional


class LinkedInClient:
    """LinkedIn API client (stub — not yet implemented)."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    async def publish_post(self, text: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("LinkedIn publishing not yet implemented")

    async def lookup_profile(self, linkedin_url: str) -> Dict[str, Any]:
        raise NotImplementedError("LinkedIn profile lookup not yet implemented")

    async def send_message(self, profile_id: str, message: str) -> Dict[str, Any]:
        raise NotImplementedError("LinkedIn messaging not yet implemented")

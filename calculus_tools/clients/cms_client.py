"""
CMS Publishing Client — Stub for MVP.

Planned capabilities:
- Blog article publishing (WordPress, Ghost, custom)
- Content scheduling
- SEO metadata management
"""

from typing import Dict, Any, Optional


class CMSClient:
    """CMS publishing client (stub — not yet implemented)."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    async def publish_article(
        self, title: str, body: str, slug: Optional[str] = None, tags: Optional[list] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("CMS publishing not yet implemented")

    async def schedule_article(self, article_id: str, publish_at: str) -> Dict[str, Any]:
        raise NotImplementedError("CMS scheduling not yet implemented")

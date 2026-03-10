"""Notion client — pages, databases, and blocks via Notion API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.notion.com/v1"


class NotionClient:
    """Async Notion API client.

    Usage::

        async with NotionClient(api_key="ntn_...") as notion:
            page = await notion.create_page(
                parent_id="db-id-here",
                title="Meeting Notes",
                properties={"Status": {"select": {"name": "Draft"}}},
            )
    """

    def __init__(self, api_key: str, *, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def create_page(self, parent_id: str, title: str, *,
                          properties: Optional[Dict[str, Any]] = None,
                          children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a page in a database or as a child of another page."""
        payload: Dict[str, Any] = {
            "parent": {"database_id": parent_id},
            "properties": {
                "title": {"title": [{"text": {"content": title}}]},
                **(properties or {}),
            },
        }
        if children:
            payload["children"] = children
        resp = await self._client.post("/pages", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update page properties."""
        resp = await self._client.patch(f"/pages/{page_id}", json={"properties": properties})
        resp.raise_for_status()
        return resp.json()

    async def query_database(self, database_id: str, *,
                              filter: Optional[Dict] = None,
                              sorts: Optional[List[Dict]] = None,
                              page_size: int = 50) -> Dict[str, Any]:
        """Query a Notion database."""
        payload: Dict[str, Any] = {"page_size": page_size}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        resp = await self._client.post(f"/databases/{database_id}/query", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page."""
        resp = await self._client.get(f"/pages/{page_id}")
        resp.raise_for_status()
        return resp.json()

    async def append_blocks(self, block_id: str, children: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Append child blocks to a page or block."""
        resp = await self._client.patch(f"/blocks/{block_id}/children", json={"children": children})
        resp.raise_for_status()
        return resp.json()

    async def search(self, query: str, *, filter_type: Optional[str] = None) -> Dict[str, Any]:
        """Search across pages and databases."""
        payload: Dict[str, Any] = {"query": query}
        if filter_type:
            payload["filter"] = {"value": filter_type, "property": "object"}
        resp = await self._client.post("/search", json=payload)
        resp.raise_for_status()
        return resp.json()

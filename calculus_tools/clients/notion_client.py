"""Notion API client for pages, databases, and blocks.

Usage::

    client = NotionClient(token="ntn_...")
    page = await client.create_page(
        parent_database_id="abc123",
        properties={"Name": "My Page"},
        children=[NotionClient.heading_block("Hello"), NotionClient.text_block("World")],
    )
    results = await client.query_database("abc123", filter={"property": "Status", "status": {"equals": "Done"}})
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionClient:
    """Async Notion API client."""

    def __init__(self, token: str) -> None:
        self.token = token
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    @staticmethod
    def text_block(content: str) -> dict[str, Any]:
        """Create a paragraph block object."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            },
        }

    @staticmethod
    def heading_block(content: str, *, level: int = 1) -> dict[str, Any]:
        """Create a heading block (level 1, 2, or 3)."""
        heading_type = f"heading_{min(max(level, 1), 3)}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [{"type": "text", "text": {"content": content}}]
            },
        }

    @staticmethod
    def _format_properties(raw: dict[str, Any]) -> dict[str, Any]:
        """Auto-format simple key-value pairs into Notion property objects.

        Strings become title (for Name/Title keys) or rich_text properties.
        Bools become checkbox, numbers become number. Dicts pass through.
        """
        formatted: dict[str, Any] = {}
        for key, value in raw.items():
            if isinstance(value, dict):
                formatted[key] = value
            elif isinstance(value, str):
                rt = [{"type": "text", "text": {"content": value}}]
                if key.lower() in ("name", "title"):
                    formatted[key] = {"title": rt}
                else:
                    formatted[key] = {"rich_text": rt}
            elif isinstance(value, bool):
                formatted[key] = {"checkbox": value}
            elif isinstance(value, (int, float)):
                formatted[key] = {"number": value}
            else:
                formatted[key] = value
        return formatted

    async def create_page(
        self,
        *,
        parent_database_id: str | None = None,
        parent_page_id: str | None = None,
        properties: dict[str, Any],
        children: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new page in a database or under a parent page."""
        if parent_database_id:
            parent = {"database_id": parent_database_id}
        elif parent_page_id:
            parent = {"page_id": parent_page_id}
        else:
            raise ValueError("Provide parent_database_id or parent_page_id")
        payload: dict[str, Any] = {
            "parent": parent,
            "properties": self._format_properties(properties),
        }
        if children:
            payload["children"] = children
        logger.info("Creating Notion page")
        resp = await self._client.post("/pages", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def update_page(
        self, page_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Update properties on an existing page."""
        logger.info("Updating Notion page %s", page_id)
        resp = await self._client.patch(
            f"/pages/{page_id}",
            json={"properties": self._format_properties(properties)},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_page(self, page_id: str) -> dict[str, Any]:
        """Retrieve a page by ID."""
        logger.debug("Fetching page %s", page_id)
        resp = await self._client.get(f"/pages/{page_id}")
        resp.raise_for_status()
        return resp.json()

    async def query_database(
        self,
        database_id: str,
        *,
        filter: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Query a Notion database with optional filter and sorts."""
        payload: dict[str, Any] = {"page_size": page_size}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        logger.debug("Querying database %s", database_id)
        resp = await self._client.post(
            f"/databases/{database_id}/query", json=payload
        )
        resp.raise_for_status()
        return resp.json()

    async def search(
        self, query: str = "", *, filter_type: str | None = None, page_size: int = 100
    ) -> dict[str, Any]:
        """Search pages and databases."""
        payload: dict[str, Any] = {"query": query, "page_size": page_size}
        if filter_type:
            payload["filter"] = {"value": filter_type, "property": "object"}
        logger.debug("Searching Notion for '%s'", query)
        resp = await self._client.post("/search", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def append_blocks(
        self, block_id: str, children: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Append child blocks to a page or block."""
        logger.info("Appending %d blocks to %s", len(children), block_id)
        resp = await self._client.patch(
            f"/blocks/{block_id}/children", json={"children": children}
        )
        resp.raise_for_status()
        return resp.json()

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """Retrieve database metadata."""
        logger.debug("Fetching database %s", database_id)
        resp = await self._client.get(f"/databases/{database_id}")
        resp.raise_for_status()
        return resp.json()

    async def list_databases(self, *, page_size: int = 100) -> dict[str, Any]:
        """List all databases the integration has access to via search."""
        return await self.search(filter_type="database", page_size=page_size)

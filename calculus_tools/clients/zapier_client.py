"""Zapier webhook and NLA (Natural Language Actions) client.

Usage::

    client = ZapierClient(nla_api_key="sk-ak-...")
    client.register_webhook("new_lead", "https://hooks.zapier.com/hooks/catch/123/abc/")
    await client.trigger("new_lead", {"email": "alice@example.com", "source": "website"})
    actions = await client.list_actions()
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

NLA_BASE_URL = "https://nla.zapier.com/api/v1"


class ZapierClient:
    """Async Zapier webhook trigger and NLA client."""

    def __init__(self, *, nla_api_key: str | None = None) -> None:
        self.nla_api_key = nla_api_key
        self._webhooks: dict[str, str] = {}
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if nla_api_key:
            headers["x-api-key"] = nla_api_key
        self._client = httpx.AsyncClient(headers=headers, timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    def register_webhook(self, name: str, url: str) -> None:
        """Register a webhook URL under a friendly name for later triggering."""
        logger.info("Registered webhook '%s' -> %s", name, url)
        self._webhooks[name] = url

    async def trigger(
        self, name: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Trigger a registered webhook by name with an optional JSON payload."""
        url = self._webhooks.get(name)
        if not url:
            raise KeyError(
                f"Webhook '{name}' not registered. "
                f"Available: {list(self._webhooks.keys())}"
            )
        return await self.trigger_url(url, data)

    async def trigger_url(
        self, url: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """POST directly to an arbitrary webhook URL."""
        logger.info("Triggering webhook: %s", url)
        resp = await self._client.post(url, json=data or {})
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": resp.status_code, "text": resp.text}

    def _ensure_nla(self) -> None:
        if not self.nla_api_key:
            raise ValueError("nla_api_key is required for NLA operations")

    async def list_actions(self) -> list[dict[str, Any]]:
        """List all exposed NLA actions for the authenticated user."""
        self._ensure_nla()
        logger.debug("Listing NLA actions")
        resp = await self._client.get(
            f"{NLA_BASE_URL}/exposed/",
            headers={"x-api-key": self.nla_api_key or ""},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])

    async def execute_action(
        self,
        action_id: str,
        instructions: str,
        *,
        params: dict[str, Any] | None = None,
        preview_only: bool = False,
    ) -> dict[str, Any]:
        """Execute (or preview) an NLA action by ID.

        Args:
            action_id: The exposed action ID from list_actions.
            instructions: Natural-language instruction for the action.
            params: Optional structured parameters to pass.
            preview_only: If True, returns what would happen without executing.
        """
        self._ensure_nla()
        endpoint = "preview" if preview_only else "execute"
        url = f"{NLA_BASE_URL}/exposed/{action_id}/{endpoint}/"
        payload: dict[str, Any] = {"instructions": instructions}
        if params:
            payload["params"] = params
        logger.info(
            "%s NLA action %s: %s",
            "Previewing" if preview_only else "Executing",
            action_id,
            instructions[:80],
        )
        resp = await self._client.post(
            url,
            json=payload,
            headers={"x-api-key": self.nla_api_key or ""},
        )
        resp.raise_for_status()
        return resp.json()

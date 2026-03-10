"""Zapier client — trigger webhooks and manage Zap executions."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ZapierClient:
    """Async Zapier REST Hooks / NLA client.

    Usage::

        async with ZapierClient(api_key="zk_...") as zap:
            await zap.trigger_webhook("https://hooks.zapier.com/hooks/catch/...", {"lead": "data"})
    """

    BASE_URL = "https://nla.zapier.com/api/v1"

    def __init__(self, api_key: str, *, timeout: float = 30.0):
        self._headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        self._timeout = timeout
        self._client = httpx.AsyncClient(headers=self._headers, timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def trigger_webhook(self, webhook_url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fire a Zapier webhook (catch hook) with arbitrary data."""
        resp = await self._client.post(webhook_url, json=data)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok", "text": resp.text}

    async def list_actions(self) -> Dict[str, Any]:
        """List available NLA actions for this API key."""
        resp = await self._client.get(f"{self.BASE_URL}/exposed/")
        resp.raise_for_status()
        return resp.json()

    async def execute_action(self, action_id: str, instructions: str,
                              *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute an exposed NLA action by ID with natural-language instructions."""
        payload: Dict[str, Any] = {"instructions": instructions}
        if params:
            payload["params"] = params
        resp = await self._client.post(
            f"{self.BASE_URL}/exposed/{action_id}/execute/",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_execution_log(self, action_id: str, execution_id: str) -> Dict[str, Any]:
        """Retrieve execution log for a specific action run."""
        resp = await self._client.get(
            f"{self.BASE_URL}/execution-log/{action_id}/{execution_id}/",
        )
        resp.raise_for_status()
        return resp.json()

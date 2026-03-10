"""Stripe client — payment links, invoices, customers, subscriptions via Stripe API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.stripe.com/v1"


class StripeClient:
    """Async Stripe API client.

    Usage::

        async with StripeClient(api_key="sk_live_...") as stripe:
            link = await stripe.create_payment_link(
                price_id="price_xxx", quantity=1,
            )
            print(link["url"])
    """

    def __init__(self, api_key: str, *, timeout: float = 30.0):
        self._client = httpx.AsyncClient(
            base_url=_API,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self._client.post(path, data=data)
        resp.raise_for_status()
        return resp.json()

    async def _get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def create_customer(self, email: str, name: str = "", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a Stripe customer."""
        data: Dict[str, Any] = {"email": email}
        if name:
            data["name"] = name
        if metadata:
            for k, v in metadata.items():
                data[f"metadata[{k}]"] = v
        return await self._post("/customers", data)

    async def create_payment_link(self, price_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Create a payment link for a price."""
        return await self._post("/payment_links", {
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": quantity,
        })

    async def create_invoice(self, customer_id: str, *, auto_advance: bool = True) -> Dict[str, Any]:
        """Create a draft invoice for a customer."""
        return await self._post("/invoices", {
            "customer": customer_id,
            "auto_advance": str(auto_advance).lower(),
        })

    async def add_invoice_item(self, customer_id: str, amount: int, currency: str = "usd",
                                description: str = "") -> Dict[str, Any]:
        """Add a line item to the customer's next invoice."""
        data: Dict[str, Any] = {"customer": customer_id, "amount": amount, "currency": currency}
        if description:
            data["description"] = description
        return await self._post("/invoiceitems", data)

    async def list_charges(self, *, customer: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent charges."""
        params: Dict[str, Any] = {"limit": limit}
        if customer:
            params["customer"] = customer
        result = await self._get("/charges", params)
        return result.get("data", [])

    async def create_subscription(self, customer_id: str, price_id: str) -> Dict[str, Any]:
        """Create a subscription."""
        return await self._post("/subscriptions", {
            "customer": customer_id,
            "items[0][price]": price_id,
        })

    async def get_balance(self) -> Dict[str, Any]:
        """Get current account balance."""
        return await self._get("/balance")

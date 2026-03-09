"""Stripe API client for payments, invoices, and customers.

Usage::

    client = StripeClient(api_key="sk_test_...", webhook_secret="whsec_...")
    link = await client.create_payment_link("Widget", 2500, "usd")
    customer = await client.create_customer("alice@example.com", name="Alice")
    await client.close()
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stripe.com/v1"


class StripeClient:
    """Async Stripe API client."""

    def __init__(self, api_key: str, webhook_secret: str | None = None) -> None:
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        resp = await self._client.post(path, data=data)
        resp.raise_for_status()
        return resp.json()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resp = await self._client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()

    async def create_payment_link(
        self,
        product_name: str,
        unit_amount: int,
        currency: str = "usd",
        *,
        quantity: int = 1,
    ) -> dict[str, Any]:
        """Create a price for an ad-hoc product, then generate a payment link."""
        logger.info("Creating payment link for %s (%d %s)", product_name, unit_amount, currency)
        price = await self._post("/prices", {
            "unit_amount": unit_amount,
            "currency": currency,
            "product_data[name]": product_name,
        })
        link = await self._post("/payment_links", {
            "line_items[0][price]": price["id"],
            "line_items[0][quantity]": quantity,
        })
        logger.debug("Payment link: %s", link.get("url"))
        return link

    async def create_invoice(
        self,
        customer_id: str,
        items: list[dict[str, Any]],
        *,
        auto_advance: bool = True,
    ) -> dict[str, Any]:
        """Create an invoice with line items and optionally finalize it."""
        logger.info("Creating invoice for customer %s with %d items", customer_id, len(items))
        invoice = await self._post("/invoices", {
            "customer": customer_id,
            "auto_advance": str(auto_advance).lower(),
        })
        for item in items:
            await self._post("/invoiceitems", {
                "customer": customer_id,
                "invoice": invoice["id"],
                "amount": item["amount"],
                "currency": item.get("currency", "usd"),
                "description": item.get("description", ""),
            })
        logger.debug("Invoice %s created", invoice["id"])
        return invoice

    async def get_payment_status(self, payment_intent_id: str) -> dict[str, Any]:
        """Retrieve the status of a PaymentIntent."""
        logger.debug("Fetching payment intent %s", payment_intent_id)
        return await self._get(f"/payment_intents/{payment_intent_id}")

    async def list_payments(
        self, *, limit: int = 10, starting_after: str | None = None
    ) -> dict[str, Any]:
        """List recent PaymentIntents."""
        params: dict[str, Any] = {"limit": limit}
        if starting_after:
            params["starting_after"] = starting_after
        logger.debug("Listing payments (limit=%d)", limit)
        return await self._get("/payment_intents", params)

    async def create_customer(
        self, email: str, *, name: str | None = None, metadata: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Create a new Stripe customer."""
        payload: dict[str, Any] = {"email": email}
        if name:
            payload["name"] = name
        if metadata:
            for k, v in metadata.items():
                payload[f"metadata[{k}]"] = v
        logger.info("Creating customer %s", email)
        return await self._post("/customers", payload)

    def verify_webhook(
        self, payload: bytes, sig_header: str, *, tolerance: int = 300
    ) -> bool:
        """Verify a Stripe webhook signature (HMAC-SHA256).

        Returns True if the signature is valid and within the time tolerance.
        """
        if not self.webhook_secret:
            raise ValueError("webhook_secret is required for signature verification")
        parts = dict(item.split("=", 1) for item in sig_header.split(","))
        timestamp = parts.get("t", "")
        expected_sig = parts.get("v1", "")
        if abs(time.time() - int(timestamp)) > tolerance:
            logger.warning("Webhook timestamp outside tolerance")
            return False
        signed_payload = f"{timestamp}.".encode() + payload
        computed = hmac.new(
            self.webhook_secret.encode(), signed_payload, hashlib.sha256
        ).hexdigest()
        valid = hmac.compare_digest(computed, expected_sig)
        if not valid:
            logger.warning("Webhook signature mismatch")
        return valid

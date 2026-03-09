"""
Stripe Payment Client — Stub for MVP.

Planned capabilities:
- Payment link creation
- Invoice generation and auto-sending
- Payment status tracking
- Customer management
- Webhook signature verification
"""

from typing import Dict, Any, Optional, List


class StripeClient:
    """Stripe API client (stub — not yet implemented)."""

    def __init__(
        self, api_key: str, webhook_secret: Optional[str] = None
    ):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    async def create_payment_link(
        self,
        amount_cents: int,
        currency: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Stripe create_payment_link not yet implemented")

    async def create_invoice(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        auto_send: bool = False,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Stripe create_invoice not yet implemented")

    async def get_payment_status(
        self, payment_intent_id: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Stripe get_payment_status not yet implemented")

    async def list_payments(
        self, customer_id: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Stripe list_payments not yet implemented")

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Stripe create_customer not yet implemented")

    async def verify_webhook(
        self, payload: str, signature: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Stripe verify_webhook not yet implemented")

"""Twilio REST API client for SMS and WhatsApp messaging.

Usage::

    client = TwilioSMSClient("ACXXX", "auth_token", "+15551234567")
    await client.send_sms("+15559876543", "Hello from calculus-tools!")
    await client.send_whatsapp("+15559876543", "WhatsApp hello!")
    await client.close()
"""
from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.twilio.com/2010-04-01"


class TwilioSMSClient:
    """Async Twilio REST API client for SMS / WhatsApp."""

    def __init__(
        self, account_sid: str, auth_token: str, from_number: str
    ) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        credentials = base64.b64encode(
            f"{account_sid}:{auth_token}".encode()
        ).decode()
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Basic {credentials}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    @property
    def _messages_url(self) -> str:
        return f"/Accounts/{self.account_sid}/Messages.json"

    async def send_sms(
        self, to: str, body: str, *, from_number: str | None = None
    ) -> dict[str, Any]:
        """Send a single SMS message."""
        payload = {
            "To": to,
            "From": from_number or self.from_number,
            "Body": body,
        }
        logger.info("Sending SMS to %s", to)
        resp = await self._client.post(self._messages_url, data=payload)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("SMS SID: %s", data.get("sid"))
        return data

    async def send_whatsapp(
        self, to: str, body: str, *, from_number: str | None = None
    ) -> dict[str, Any]:
        """Send a WhatsApp message (auto-prefixes whatsapp: to numbers)."""
        wa_to = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        source = from_number or self.from_number
        wa_from = source if source.startswith("whatsapp:") else f"whatsapp:{source}"
        payload = {"To": wa_to, "From": wa_from, "Body": body}
        logger.info("Sending WhatsApp to %s", wa_to)
        resp = await self._client.post(self._messages_url, data=payload)
        resp.raise_for_status()
        return resp.json()

    async def send_batch_sms(
        self, recipients: list[str], body: str
    ) -> list[dict[str, Any]]:
        """Send the same SMS body to multiple recipients sequentially."""
        results: list[dict[str, Any]] = []
        for to in recipients:
            logger.info("Batch SMS %d/%d to %s", len(results) + 1, len(recipients), to)
            result = await self.send_sms(to, body)
            results.append(result)
        return results

    async def check_delivery_status(self, message_sid: str) -> dict[str, Any]:
        """Fetch current delivery status of a sent message."""
        url = f"/Accounts/{self.account_sid}/Messages/{message_sid}.json"
        logger.debug("Checking delivery status for %s", message_sid)
        resp = await self._client.get(url)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("Message %s status: %s", message_sid, data.get("status"))
        return data

    async def list_messages(
        self,
        *,
        to: str | None = None,
        from_: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent messages with optional filters."""
        params: dict[str, Any] = {"PageSize": min(limit, 1000)}
        if to:
            params["To"] = to
        if from_:
            params["From"] = from_
        logger.debug("Listing messages (limit=%d)", limit)
        resp = await self._client.get(self._messages_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("messages", [])

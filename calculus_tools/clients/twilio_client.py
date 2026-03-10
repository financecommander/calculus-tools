"""Twilio client — SMS, MMS, voice calls, and lookups via Twilio REST API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_API = "https://api.twilio.com/2010-04-01"


class TwilioClient:
    """Async Twilio REST API client.

    Usage::

        async with TwilioClient(
            account_sid="AC...",
            auth_token="...",
            from_number="+18338472291",
        ) as twilio:
            await twilio.send_sms("+15551234567", "Hello from swarm!")
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str, *, timeout: float = 30.0):
        self._sid = account_sid
        self._from = from_number
        self._client = httpx.AsyncClient(
            base_url=f"{_API}/Accounts/{account_sid}",
            auth=(account_sid, auth_token),
            timeout=timeout,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    async def send_sms(self, to: str, body: str, *, media_url: Optional[str] = None) -> Dict[str, Any]:
        """Send an SMS or MMS message."""
        data = {"From": self._from, "To": to, "Body": body}
        if media_url:
            data["MediaUrl"] = media_url
        resp = await self._client.post("/Messages.json", data=data)
        resp.raise_for_status()
        return resp.json()

    async def make_call(self, to: str, twiml: str) -> Dict[str, Any]:
        """Initiate an outbound voice call with TwiML instructions."""
        data = {"From": self._from, "To": to, "Twiml": twiml}
        resp = await self._client.post("/Calls.json", data=data)
        resp.raise_for_status()
        return resp.json()

    async def lookup(self, phone: str, *, fields: str = "carrier") -> Dict[str, Any]:
        """Lookup phone number info."""
        resp = await self._client.get(
            f"https://lookups.twilio.com/v2/PhoneNumbers/{phone}",
            params={"Fields": fields},
        )
        resp.raise_for_status()
        return resp.json()

    async def list_messages(self, *, to: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent messages."""
        params: Dict[str, Any] = {"PageSize": limit}
        if to:
            params["To"] = to
        resp = await self._client.get("/Messages.json", params=params)
        resp.raise_for_status()
        return resp.json().get("messages", [])

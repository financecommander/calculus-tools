"""
Twilio SMS / WhatsApp Client — Stub for MVP.

Planned capabilities:
- SMS sending (single and batch)
- WhatsApp messaging with media support
- Delivery status tracking
- Message history listing
"""

from typing import Dict, Any, Optional, List


class TwilioSMSClient:
    """Twilio SMS client (stub — not yet implemented)."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    async def send_sms(
        self, to: str, body: str, from_number: Optional[str] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("Twilio send_sms not yet implemented")

    async def send_whatsapp(
        self, to: str, body: str, media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("Twilio send_whatsapp not yet implemented")

    async def send_batch_sms(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Twilio send_batch_sms not yet implemented")

    async def check_delivery_status(
        self, message_sid: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Twilio check_delivery_status not yet implemented")

    async def list_messages(
        self,
        date_sent: Optional[str] = None,
        to: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Twilio list_messages not yet implemented")

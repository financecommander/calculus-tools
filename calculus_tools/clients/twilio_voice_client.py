"""
Twilio Voice Client — Stub for MVP.

Planned capabilities:
- Outbound voice calls with TwiML or URL
- Text-to-speech audio generation
- Recording retrieval and transcription
- Call history listing
"""

from typing import Dict, Any, Optional, List


class TwilioVoiceClient:
    """Twilio Voice client (stub — not yet implemented)."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: Optional[str] = None,
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number

    async def make_call(
        self,
        to: str,
        twiml: Optional[str] = None,
        url: Optional[str] = None,
        record: bool = False,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Twilio make_call not yet implemented")

    async def text_to_speech(
        self, text: str, voice: str = "alice", language: str = "en-US"
    ) -> bytes:
        raise NotImplementedError("Twilio text_to_speech not yet implemented")

    async def transcribe_recording(
        self, recording_sid: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Twilio transcribe_recording not yet implemented")

    async def get_recording(self, recording_sid: str) -> bytes:
        raise NotImplementedError("Twilio get_recording not yet implemented")

    async def list_calls(
        self, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Twilio list_calls not yet implemented")

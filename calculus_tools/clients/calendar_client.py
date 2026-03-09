"""
Google Calendar Client — Stub for MVP.

Planned capabilities:
- Event creation with attendees and location
- Event listing, updating, and deletion
- Free/busy availability checks
- Google Meet link generation
"""

from typing import Dict, Any, Optional, List


class CalendarClient:
    """Google Calendar API client (stub — not yet implemented)."""

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        service_account_key: Optional[str] = None,
    ):
        self.credentials_json = credentials_json
        self.service_account_key = service_account_key

    async def create_event(
        self,
        summary: str,
        start: str,
        end: str,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("Calendar create_event not yet implemented")

    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("Calendar list_events not yet implemented")

    async def update_event(
        self, event_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        raise NotImplementedError("Calendar update_event not yet implemented")

    async def delete_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> Dict[str, Any]:
        raise NotImplementedError("Calendar delete_event not yet implemented")

    async def check_availability(
        self, attendees: List[str], time_min: str, time_max: str
    ) -> Dict[str, Any]:
        raise NotImplementedError("Calendar check_availability not yet implemented")

    async def create_meeting_link(self) -> str:
        raise NotImplementedError("Calendar create_meeting_link not yet implemented")

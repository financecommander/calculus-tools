"""Google Workspace client — Gmail, Calendar, and Drive via Google REST APIs."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import base64

import httpx

logger = logging.getLogger(__name__)


class GoogleWorkspaceClient:
    """Async Google Workspace API client (Gmail, Calendar, Drive).

    Usage::

        async with GoogleWorkspaceClient(access_token="ya29...") as gw:
            await gw.send_email("user@example.com", "Subject", "Body text")
            events = await gw.list_calendar_events()
    """

    def __init__(self, access_token: str, *, timeout: float = 30.0):
        self._headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        self._timeout = timeout
        self._client = httpx.AsyncClient(headers=self._headers, timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self._client.aclose()

    # ── Gmail ─────────────────────────────────────────────────────

    async def send_email(self, to: str, subject: str, body: str, *, from_name: str = "") -> Dict[str, Any]:
        """Send an email via Gmail API."""
        message = f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}"
        raw = base64.urlsafe_b64encode(message.encode()).decode()
        resp = await self._client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            json={"raw": raw},
        )
        resp.raise_for_status()
        return resp.json()

    async def list_emails(self, *, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        """List emails matching a query."""
        params: Dict[str, Any] = {"maxResults": max_results}
        if query:
            params["q"] = query
        resp = await self._client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def get_email(self, message_id: str) -> Dict[str, Any]:
        """Get a specific email by ID."""
        resp = await self._client.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
        )
        resp.raise_for_status()
        return resp.json()

    # ── Calendar ──────────────────────────────────────────────────

    async def list_calendar_events(self, *, calendar_id: str = "primary",
                                    max_results: int = 10,
                                    time_min: Optional[str] = None) -> Dict[str, Any]:
        """List upcoming calendar events."""
        params: Dict[str, Any] = {"maxResults": max_results, "singleEvents": True, "orderBy": "startTime"}
        if time_min:
            params["timeMin"] = time_min
        resp = await self._client.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def create_calendar_event(self, summary: str, start: str, end: str,
                                     *, calendar_id: str = "primary",
                                     description: str = "",
                                     attendees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a calendar event."""
        payload: Dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start},
            "end": {"dateTime": end},
        }
        if description:
            payload["description"] = description
        if attendees:
            payload["attendees"] = [{"email": e} for e in attendees]
        resp = await self._client.post(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Drive ─────────────────────────────────────────────────────

    async def list_files(self, *, query: str = "", page_size: int = 20) -> Dict[str, Any]:
        """List Google Drive files."""
        params: Dict[str, Any] = {"pageSize": page_size}
        if query:
            params["q"] = query
        resp = await self._client.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def create_doc(self, title: str) -> Dict[str, Any]:
        """Create a new Google Doc."""
        resp = await self._client.post(
            "https://docs.googleapis.com/v1/documents",
            json={"title": title},
        )
        resp.raise_for_status()
        return resp.json()

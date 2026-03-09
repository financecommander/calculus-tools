"""Google Workspace client covering Calendar, Drive, and Gmail APIs.

Usage::

    client = GoogleWorkspaceClient(access_token="ya29.a0...")
    events = await client.list_events(calendar_id="primary")
    files = await client.list_files(q="mimeType='application/pdf'")
    emails = await client.list_emails(query="is:unread")
    await client.close()
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CALENDAR_URL = "https://www.googleapis.com/calendar/v3"
DRIVE_URL = "https://www.googleapis.com/drive/v3"
GMAIL_URL = "https://gmail.googleapis.com/gmail/v1"


class GoogleWorkspaceClient:
    """Async client for Google Calendar, Drive, and Gmail APIs."""

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token
        self._client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ── Calendar ───────────────────────────────────────────────────────

    async def list_events(
        self,
        calendar_id: str = "primary",
        *,
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """List upcoming calendar events."""
        params: dict[str, Any] = {
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        }
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        logger.debug("Listing events for calendar %s", calendar_id)
        resp = await self._client.get(
            f"{CALENDAR_URL}/calendars/{calendar_id}/events", params=params
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    async def create_event(
        self,
        calendar_id: str = "primary",
        *,
        summary: str,
        start: str,
        end: str,
        description: str = "",
        attendees: list[str] | None = None,
        timezone: str = "UTC",
    ) -> dict[str, Any]:
        """Create a calendar event. start/end are ISO-8601 datetime strings."""
        event: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start, "timeZone": timezone},
            "end": {"dateTime": end, "timeZone": timezone},
        }
        if attendees:
            event["attendees"] = [{"email": e} for e in attendees]
        logger.info("Creating event '%s'", summary)
        resp = await self._client.post(
            f"{CALENDAR_URL}/calendars/{calendar_id}/events", json=event
        )
        resp.raise_for_status()
        return resp.json()

    async def delete_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> int:
        """Delete a calendar event. Returns HTTP status code."""
        logger.info("Deleting event %s", event_id)
        resp = await self._client.delete(
            f"{CALENDAR_URL}/calendars/{calendar_id}/events/{event_id}"
        )
        resp.raise_for_status()
        return resp.status_code

    # ── Drive ──────────────────────────────────────────────────────────

    async def list_files(
        self,
        *,
        q: str | None = None,
        page_size: int = 100,
        fields: str = "files(id,name,mimeType,modifiedTime)",
    ) -> list[dict[str, Any]]:
        """List files in Google Drive with optional query filter."""
        params: dict[str, Any] = {"pageSize": page_size, "fields": fields}
        if q:
            params["q"] = q
        logger.debug("Listing Drive files")
        resp = await self._client.get(f"{DRIVE_URL}/files", params=params)
        resp.raise_for_status()
        return resp.json().get("files", [])

    async def create_folder(
        self, name: str, *, parent_id: str | None = None
    ) -> dict[str, Any]:
        """Create a folder in Google Drive."""
        metadata: dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]
        logger.info("Creating Drive folder '%s'", name)
        resp = await self._client.post(f"{DRIVE_URL}/files", json=metadata)
        resp.raise_for_status()
        return resp.json()

    async def get_file_metadata(
        self, file_id: str, *, fields: str = "id,name,mimeType,size,modifiedTime"
    ) -> dict[str, Any]:
        """Get metadata for a single Drive file."""
        logger.debug("Fetching metadata for file %s", file_id)
        resp = await self._client.get(
            f"{DRIVE_URL}/files/{file_id}", params={"fields": fields}
        )
        resp.raise_for_status()
        return resp.json()

    # ── Gmail ──────────────────────────────────────────────────────────

    async def list_emails(
        self,
        *,
        query: str = "",
        max_results: int = 20,
        user_id: str = "me",
    ) -> list[dict[str, Any]]:
        """List email message IDs matching a query."""
        params: dict[str, Any] = {"maxResults": max_results}
        if query:
            params["q"] = query
        logger.debug("Listing emails (query='%s')", query)
        resp = await self._client.get(
            f"{GMAIL_URL}/users/{user_id}/messages", params=params
        )
        resp.raise_for_status()
        return resp.json().get("messages", [])

    async def get_email(
        self, message_id: str, *, user_id: str = "me", fmt: str = "full"
    ) -> dict[str, Any]:
        """Retrieve a single email message."""
        logger.debug("Fetching email %s", message_id)
        resp = await self._client.get(
            f"{GMAIL_URL}/users/{user_id}/messages/{message_id}",
            params={"format": fmt},
        )
        resp.raise_for_status()
        return resp.json()

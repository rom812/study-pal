"""Google Calendar API client for direct calendar integration."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


@dataclass
class GoogleCalendarClient:
    """Direct Google Calendar API client replacing the MCP-based connector."""

    credentials_path: str | None = None
    token_path: str | None = None

    _service: object | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.credentials_path is None:
            self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if self.token_path is None:
            self.token_path = os.getenv("GOOGLE_TOKEN_PATH", "data/google_token.json")

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def _get_service(self):
        """Build and cache the Google Calendar API service."""
        if self._service is not None:
            return self._service

        if not GOOGLE_API_AVAILABLE:
            logger.warning("Google API libraries not installed. Calendar features disabled.")
            return None

        creds = self._load_credentials()
        if creds is None:
            return None

        try:
            self._service = build("calendar", "v3", credentials=creds)
            return self._service
        except Exception as exc:
            logger.warning("Failed to build Google Calendar service: %s", exc)
            return None

    def _load_credentials(self) -> "Credentials | None":
        """Load or refresh OAuth2 credentials."""
        creds = None

        # Try loading existing token
        if self.token_path and Path(self.token_path).exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, GOOGLE_CALENDAR_SCOPES)
            except Exception as exc:
                logger.warning("Failed to load token from %s: %s", self.token_path, exc)

        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
            except Exception as exc:
                logger.warning("Failed to refresh credentials: %s", exc)
                creds = None

        # If no valid creds, check if credentials file exists for new auth
        if not creds or not creds.valid:
            if not self.credentials_path or not Path(self.credentials_path).exists():
                logger.info(
                    "Google Calendar credentials not configured (%s not found). "
                    "Calendar features disabled. Run scripts/setup_google_calendar.py to set up.",
                    self.credentials_path,
                )
                return None

            try:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, GOOGLE_CALENDAR_SCOPES)
                creds = flow.run_local_server(port=0)
                self._save_token(creds)
            except Exception as exc:
                logger.warning("OAuth flow failed: %s", exc)
                return None

        return creds

    def _save_token(self, creds: "Credentials") -> None:
        """Persist token to disk for future runs."""
        if not self.token_path:
            return
        try:
            Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w") as f:
                f.write(creds.to_json())
        except Exception as exc:
            logger.warning("Failed to save token to %s: %s", self.token_path, exc)

    # ------------------------------------------------------------------
    # Public API — matches the old CalendarConnector interface
    # ------------------------------------------------------------------

    def create_event(self, payload: dict) -> None:
        """Create a calendar event.

        Accepts payload with keys: summary, description, start, end.
        Start/end should already be in Google Calendar API format:
            {"dateTime": "...", "timeZone": "..."}
        """
        service = self._get_service()
        if service is None:
            logger.info("Calendar not configured. Event creation skipped.")
            print("\u2139\ufe0f  Calendar sync skipped (not configured)")
            return

        try:
            body = {
                "summary": payload.get("summary", "Study Session"),
                "description": payload.get("description", ""),
                "start": payload.get("start", {}),
                "end": payload.get("end", {}),
            }
            calendar_id = payload.get("calendarId", "primary")
            service.events().insert(calendarId=calendar_id, body=body).execute()
            logger.debug("Created calendar event: %s", body.get("summary"))
        except Exception as exc:
            logger.warning("Failed to create calendar event: %s", exc)
            print(f"\u26a0\ufe0f  Calendar sync failed: {exc}")

    def list_events(
        self,
        time_min: str | None = None,
        time_max: str | None = None,
        calendar_id: str = "primary",
        max_results: int = 50,
    ) -> list:
        """List calendar events in a time range."""
        service = self._get_service()
        if service is None:
            return []

        try:
            kwargs = {
                "calendarId": calendar_id,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            }
            if time_min:
                kwargs["timeMin"] = time_min
            if time_max:
                kwargs["timeMax"] = time_max

            result = service.events().list(**kwargs).execute()
            return result.get("items", [])
        except Exception as exc:
            logger.warning("Failed to list calendar events: %s", exc)
            return []

    def search_events(self, query: str, calendar_id: str = "primary") -> list:
        """Search calendar events by text query."""
        service = self._get_service()
        if service is None:
            return []

        try:
            result = (
                service.events().list(calendarId=calendar_id, q=query, singleEvents=True, orderBy="startTime").execute()
            )
            return result.get("items", [])
        except Exception as exc:
            logger.warning("Failed to search calendar events: %s", exc)
            return []

    def update_event(self, event_id: str, payload: dict) -> None:
        """Update an existing calendar event."""
        service = self._get_service()
        if service is None:
            return

        try:
            calendar_id = payload.pop("calendarId", "primary")
            service.events().patch(calendarId=calendar_id, eventId=event_id, body=payload).execute()
            logger.debug("Updated calendar event: %s", event_id)
        except Exception as exc:
            logger.warning("Failed to update calendar event %s: %s", event_id, exc)

    def delete_event(self, event_id: str, calendar_id: str = "primary") -> None:
        """Delete a calendar event."""
        service = self._get_service()
        if service is None:
            return

        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            logger.debug("Deleted calendar event: %s", event_id)
        except Exception as exc:
            logger.warning("Failed to delete calendar event %s: %s", event_id, exc)

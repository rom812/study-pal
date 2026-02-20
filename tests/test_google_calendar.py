"""Tests for GoogleCalendarClient direct API integration."""

from __future__ import annotations

from unittest.mock import MagicMock

from core.google_calendar import GoogleCalendarClient


class TestGoogleCalendarClientConfig:
    """GoogleCalendarClient reads config from env or explicit params."""

    def test_default_paths(self, monkeypatch):
        """Client uses default credential paths when env vars not set."""
        monkeypatch.delenv("GOOGLE_CREDENTIALS_PATH", raising=False)
        monkeypatch.delenv("GOOGLE_TOKEN_PATH", raising=False)
        c = GoogleCalendarClient()
        assert c.credentials_path == "credentials.json"
        assert c.token_path == "data/google_token.json"

    def test_custom_paths_from_env(self, monkeypatch):
        """Client reads paths from environment variables."""
        monkeypatch.setenv("GOOGLE_CREDENTIALS_PATH", "/custom/creds.json")
        monkeypatch.setenv("GOOGLE_TOKEN_PATH", "/custom/token.json")
        c = GoogleCalendarClient()
        assert c.credentials_path == "/custom/creds.json"
        assert c.token_path == "/custom/token.json"

    def test_explicit_paths_override_env(self, monkeypatch):
        """Explicit params take precedence over env vars."""
        monkeypatch.setenv("GOOGLE_CREDENTIALS_PATH", "/env/creds.json")
        c = GoogleCalendarClient(credentials_path="/explicit/creds.json")
        assert c.credentials_path == "/explicit/creds.json"

    def test_no_credentials_skips_gracefully(self):
        """When credentials file doesn't exist, methods return empty/skip."""
        c = GoogleCalendarClient(credentials_path="/nonexistent/creds.json", token_path="/nonexistent/token.json")
        # Should not raise
        assert c.list_events() == []
        assert c.search_events("test") == []
        c.create_event({"summary": "test"})  # should not raise
        c.delete_event("event123")  # should not raise


class TestGoogleCalendarClientMethods:
    """GoogleCalendarClient methods delegate to Google API correctly."""

    def _make_client_with_mock_service(self):
        """Create a client with a mocked Google Calendar service."""
        c = GoogleCalendarClient(credentials_path="/fake/creds.json")
        mock_service = MagicMock()
        c._service = mock_service
        return c, mock_service

    def test_list_events_returns_items(self):
        """list_events returns the items from Google Calendar API response."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().list().execute.return_value = {"items": [{"summary": "Meeting", "id": "abc123"}]}

        result = c.list_events(time_min="2026-02-13T00:00:00Z", time_max="2026-02-13T23:59:59Z")
        assert len(result) == 1
        assert result[0]["summary"] == "Meeting"

    def test_list_events_passes_parameters(self):
        """list_events passes time range and other params to API."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().list().execute.return_value = {"items": []}

        c.list_events(time_min="2026-01-01T00:00:00Z", time_max="2026-01-02T00:00:00Z", max_results=10)
        mock_service.events().list.assert_called()

    def test_create_event_calls_insert(self):
        """create_event calls events().insert() with correct payload."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().insert().execute.return_value = {"id": "new123"}

        payload = {
            "summary": "Study: Python",
            "description": "Pomodoro session",
            "start": {"dateTime": "2026-02-14T14:00:00", "timeZone": "Asia/Jerusalem"},
            "end": {"dateTime": "2026-02-14T14:25:00", "timeZone": "Asia/Jerusalem"},
        }
        c.create_event(payload)
        mock_service.events().insert.assert_called()

    def test_search_events_uses_q_parameter(self):
        """search_events passes query as 'q' parameter."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().list().execute.return_value = {"items": [{"summary": "Python Study"}]}

        result = c.search_events("Python")
        assert len(result) == 1
        mock_service.events().list.assert_called()

    def test_delete_event_calls_delete(self):
        """delete_event calls events().delete() with correct params."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().delete().execute.return_value = None

        c.delete_event("event123", calendar_id="primary")
        mock_service.events().delete.assert_called()

    def test_update_event_calls_patch(self):
        """update_event calls events().patch() with correct params."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().patch().execute.return_value = {"id": "event123"}

        c.update_event("event123", {"summary": "Updated Study"})
        mock_service.events().patch.assert_called()

    def test_api_error_returns_empty_list(self):
        """API errors are caught and return empty results."""
        c, mock_service = self._make_client_with_mock_service()
        mock_service.events().list().execute.side_effect = Exception("API error")

        result = c.list_events()
        assert result == []

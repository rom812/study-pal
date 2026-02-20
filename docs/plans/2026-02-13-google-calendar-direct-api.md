# Replace MCP with Direct Google Calendar API

**Date:** 2026-02-13
**Goal:** Remove the MCP middleman and connect to Google Calendar API directly using `google-api-python-client`, simplifying the architecture from 3 layers to 1.

---

## Current State (MCP-based)

```
Python App → HTTP → MCP Server (Node.js Docker) → Google Calendar API
```

**Files involved:**
- `core/mcp_connectors.py` — CalendarConnector class (MCP client)
- `calendar-mcp/` — Docker sidecar (Dockerfile, .env.example, SETUP.md)
- `docker-compose.yml` — orchestrates the MCP sidecar
- `agents/scheduler_agent.py` — uses CalendarConnector
- `core/workflow_nodes.py` — instantiates CalendarConnector
- `tests/test_mcp_connectors.py` — MCP connector tests
- `tests/test_calendar_integration.py` — integration tests (mock MCP)
- `.env` — MCP endpoint/token vars + OAuth credentials

## Target State (Direct API)

```
Python App → google-api-python-client → Google Calendar API
```

---

## Implementation Plan

### Task 1: Create `core/google_calendar.py` (new GoogleCalendarClient)

Replace `core/mcp_connectors.py` with a direct Google Calendar API client.

**The new `GoogleCalendarClient` class must expose the same interface the codebase already uses:**
- `create_event(payload: dict) -> None`
- `list_events(time_min, time_max, calendar_id, max_results) -> list`
- `search_events(query, calendar_id) -> list`
- `update_event(event_id, payload) -> None`
- `delete_event(event_id, calendar_id) -> None`

**Authentication:**
- Use OAuth 2.0 with `google-auth-oauthlib` for the Desktop flow
- Store token in `data/google_token.json` (auto-refresh)
- Read `credentials.json` path from env var `GOOGLE_CREDENTIALS_PATH` (default: `credentials.json`)
- Graceful degradation: if no credentials configured, all methods return empty/skip (same as current MCP behavior)

**Key design decisions:**
- Synchronous methods (matching current CalendarConnector interface) — no asyncio gymnastics
- No Docker sidecar needed
- No MCP dependency

### Task 2: Update `agents/scheduler_agent.py`

- Change type hint from `object | None` to `GoogleCalendarClient | None` for `calendar_connector`
- Update `_build_calendar_event_payload()` to use Google Calendar API format:
  ```python
  {
      "summary": "Study: Python",
      "description": "Pomodoro study session for Python",
      "start": {"dateTime": "2026-02-14T14:00:00", "timeZone": "Asia/Jerusalem"},
      "end": {"dateTime": "2026-02-14T14:25:00", "timeZone": "Asia/Jerusalem"},
  }
  ```
- The rest of the scheduler logic stays the same

### Task 3: Update `core/workflow_nodes.py`

- Replace `from core.mcp_connectors import CalendarConnector` with `from core.google_calendar import GoogleCalendarClient`
- Replace `CalendarConnector()` with `GoogleCalendarClient()` (2 occurrences in `scheduler_agent_node`)

### Task 4: Update `requirements.txt`

**Add:**
```
google-api-python-client>=2.100.0
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
```

**Remove (if present):**
- `mcp` (not currently listed but may be installed)

### Task 5: Update `.env` and environment config

**Remove MCP-specific vars:**
```
GOOGLE_CALENDAR_MCP_ENABLED
GOOGLE_CALENDAR_MCP_URL
```

**Keep OAuth vars** (still needed for direct API):
```
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_PROJECT_ID
```

**Add:**
```
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=data/google_token.json
```

### Task 6: Update `docker-compose.yml`

- Remove the `calendar-mcp` service entirely
- Remove `depends_on: calendar-mcp` from the `api` service
- Remove `GOOGLE_CALENDAR_MCP_URL` env var from the `api` service

### Task 7: Delete MCP-related files

- Delete `calendar-mcp/` directory (Dockerfile, .env.example, SETUP.md)
- Delete `core/mcp_connectors.py`

### Task 8: Update tests

**Replace `tests/test_mcp_connectors.py`** with `tests/test_google_calendar.py`:
- Test GoogleCalendarClient config (credentials path, graceful skip)
- Test list_events, create_event delegation (mocked Google API)

**Update `tests/test_calendar_integration.py`**:
- Update MockCalendarConnector to match new GoogleCalendarClient interface
- Event payload format changes (nested start/end with timeZone)
- Remove MCP-specific references

### Task 9: Create `credentials.json` setup helper

- Add a `scripts/setup_google_calendar.py` that:
  1. Reads OAuth client ID/secret from env
  2. Generates `credentials.json` in the expected format
  3. Runs the OAuth flow to create `data/google_token.json`
- Update docs (README or a new GOOGLE_CALENDAR_SETUP.md)

---

## Files Changed Summary

| Action | File |
|--------|------|
| CREATE | `core/google_calendar.py` |
| CREATE | `tests/test_google_calendar.py` |
| CREATE | `scripts/setup_google_calendar.py` |
| MODIFY | `agents/scheduler_agent.py` |
| MODIFY | `core/workflow_nodes.py` |
| MODIFY | `requirements.txt` |
| MODIFY | `docker-compose.yml` |
| MODIFY | `.env` |
| MODIFY | `tests/test_calendar_integration.py` |
| DELETE | `core/mcp_connectors.py` |
| DELETE | `tests/test_mcp_connectors.py` |
| DELETE | `calendar-mcp/` (entire directory) |

---

## Risk & Rollback

- **Low risk:** The interface stays the same — `create_event`, `list_events`, etc.
- **Rollback:** Git revert to pre-change commit
- **Testing:** All existing integration tests are updated to verify same behavior
- **Graceful degradation preserved:** If Google credentials not configured, everything still works without calendar

# Self-Hosted Google Calendar MCP Server Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the unreliable external Google Calendar MCP dependency with a self-hosted `nspady/google-calendar-mcp` sidecar running in HTTP transport mode, then extend the `CalendarConnector` to support listing events and checking availability before scheduling.

**Architecture:** Run `nspady/google-calendar-mcp` as a Docker sidecar alongside the StudyPal API. The existing `CalendarConnector` in `core/mcp_connectors.py` already speaks MCP over Streamable HTTP — it just needs to point at our own server and grow support for `list-events` and `search-events` tools in addition to `create-event`.

**Tech Stack:** Docker Compose, Node 20 (MCP server image), Python MCP SDK (`mcp` package), Google Calendar API (OAuth 2.0 Desktop flow), pytest.

**Repo:** https://github.com/nspady/google-calendar-mcp (979 stars, MIT, updated Feb 2026, MCP SDK `^1.12.1`)

---

## Task 1: Add the Google Calendar MCP Sidecar to Docker Compose

**Files:**
- Create: `calendar-mcp/Dockerfile`
- Modify: `docker-compose.yml`
- Create: `calendar-mcp/.env.example`

**Step 1: Create `calendar-mcp/Dockerfile`**

```dockerfile
# calendar-mcp/Dockerfile
FROM node:20-slim

WORKDIR /app

# Install the published npm package
RUN npm install @cocal/google-calendar-mcp@latest

# OAuth credentials and tokens are mounted at runtime
VOLUME ["/app/credentials"]

# HTTP transport on port 3000
EXPOSE 3000

# Start in HTTP transport mode
CMD ["node", "node_modules/@cocal/google-calendar-mcp/build/index.js", "--transport", "http", "--port", "3000", "--host", "0.0.0.0"]
```

**Step 2: Create `calendar-mcp/.env.example`**

```env
# Google OAuth — Desktop App credentials from Google Cloud Console
# See: https://github.com/nspady/google-calendar-mcp#google-cloud-setup
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

**Step 3: Add the sidecar service to `docker-compose.yml`**

The existing file is minimal (just the api service). Add the calendar-mcp service:

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_CALENDAR_MCP_URL=http://calendar-mcp:3000/mcp
    volumes:
      - ./data:/app/data
    depends_on:
      calendar-mcp:
        condition: service_started

  calendar-mcp:
    build: ./calendar-mcp
    ports:
      - "3000:3000"
    volumes:
      - ./calendar-mcp/credentials:/app/credentials
    environment:
      - GOOGLE_OAUTH_CLIENT_ID=${GOOGLE_OAUTH_CLIENT_ID}
      - GOOGLE_OAUTH_CLIENT_SECRET=${GOOGLE_OAUTH_CLIENT_SECRET}
    restart: unless-stopped
```

**Step 4: Commit**

```bash
git add calendar-mcp/Dockerfile calendar-mcp/.env.example docker-compose.yml
git commit -m "feat: add google-calendar-mcp sidecar to docker-compose"
```

---

## Task 2: Add Local Dev Startup for the Calendar MCP Server

**Files:**
- Modify: `start_dev.sh`
- Modify: `.env` (document new vars)

**Step 1: Add calendar MCP startup to `start_dev.sh`**

Insert after the backend startup block (after `BACKEND_PID=$!`) and before the frontend startup. The calendar MCP server needs port 3001 in dev (frontend uses 3000):

```bash
# --- Google Calendar MCP sidecar (optional) ---
GCAL_MCP_PORT=3001
if command -v npx &>/dev/null && [ -n "${GOOGLE_CALENDAR_MCP_ENABLED:-}" ]; then
    echo "📅 Starting Google Calendar MCP server on http://localhost:$GCAL_MCP_PORT ..."
    npx -y @cocal/google-calendar-mcp --transport http --port "$GCAL_MCP_PORT" >> "$SCRIPT_DIR/logs/calendar-mcp.log" 2>&1 &
    GCAL_PID=$!
    # Quick readiness check
    for i in $(seq 1 15); do
        sleep 1
        if curl -s --connect-timeout 2 -o /dev/null "http://localhost:$GCAL_MCP_PORT" 2>/dev/null; then
            echo "   Calendar MCP ready after ${i}s (PID $GCAL_PID)"
            break
        fi
        [ $i -eq 15 ] && echo "⚠️  Calendar MCP did not respond after 15s. Check logs/calendar-mcp.log"
    done
    # Override the env var so CalendarConnector finds the local server
    export GOOGLE_CALENDAR_MCP_URL="http://localhost:$GCAL_MCP_PORT/mcp"
else
    echo "📅 Calendar MCP skipped (set GOOGLE_CALENDAR_MCP_ENABLED=1 to start)"
fi
```

Update the trap line to also kill GCAL_PID:

```bash
trap "kill $BACKEND_PID $FRONTEND_PID ${GCAL_PID:-} 2>/dev/null; exit" INT TERM
```

**Step 2: Add env vars documentation to `.env`**

Append to `.env`:

```env
# --- Google Calendar MCP (optional) ---
# Set to 1 to start the calendar MCP sidecar in dev mode
# GOOGLE_CALENDAR_MCP_ENABLED=1
# Endpoint for the MCP server (auto-set by start_dev.sh when enabled)
GOOGLE_CALENDAR_MCP_URL=http://localhost:3001/mcp
```

**Step 3: Commit**

```bash
git add start_dev.sh
git commit -m "feat: add optional calendar MCP sidecar to dev startup"
```

---

## Task 3: Generalize CalendarConnector to Support Multiple MCP Tools

Currently `CalendarConnector` only supports `create-event`. We need `list-events` and `search-events` for availability checking.

**Files:**
- Modify: `core/mcp_connectors.py`
- Test: `tests/test_mcp_connectors.py`

**Step 1: Write failing tests for the new `call_tool` method**

Create `tests/test_mcp_connectors.py`:

```python
"""Tests for CalendarConnector multi-tool support."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.mcp_connectors import CalendarConnector


class TestCalendarConnectorConfig:
    """CalendarConnector reads config from env or explicit params."""

    def test_explicit_endpoint(self):
        c = CalendarConnector(endpoint="http://localhost:3001/mcp")
        assert c.endpoint == "http://localhost:3001/mcp"

    def test_endpoint_from_env(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CALENDAR_MCP_URL", "http://mcp:3000/mcp")
        c = CalendarConnector()
        assert c.endpoint == "http://mcp:3000/mcp"

    def test_no_endpoint_skips_gracefully(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_CALENDAR_MCP_URL", raising=False)
        monkeypatch.delenv("GOOGLE_CALENDAR_MCP_HTTP_URL", raising=False)
        monkeypatch.delenv("GOOGLE_CALENDAR_MCP_ENDPOINT", raising=False)
        c = CalendarConnector()
        assert c.endpoint is None
        # create_event should not raise, just skip
        c.create_event({"summary": "test"})


class TestCalendarConnectorCallTool:
    """CalendarConnector.call_tool dispatches arbitrary MCP tool calls."""

    def test_call_tool_raises_without_endpoint(self):
        c = CalendarConnector(endpoint=None)
        result = c.call_tool("list-events", {"timeMin": "2026-01-01"})
        assert result is None  # graceful skip

    def test_call_tool_returns_none_without_mcp_library(self, monkeypatch):
        monkeypatch.setattr("core.mcp_connectors.MCP_AVAILABLE", False)
        c = CalendarConnector(endpoint="http://localhost:3000/mcp")
        result = c.call_tool("list-events", {})
        assert result is None


class TestListEvents:
    """CalendarConnector.list_events convenience wrapper."""

    def test_list_events_delegates_to_call_tool(self):
        c = CalendarConnector(endpoint="http://localhost:3001/mcp")
        with patch.object(c, "call_tool", return_value=[]) as mock:
            c.list_events(time_min="2026-02-13T00:00:00", time_max="2026-02-13T23:59:59")
            mock.assert_called_once()
            args = mock.call_args
            assert args[0][0] == "list-events"
            assert "timeMin" in args[0][1]
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_mcp_connectors.py -v
```

Expected: FAIL (no `call_tool` or `list_events` methods yet).

**Step 3: Implement `call_tool` and `list_events` on CalendarConnector**

Add to `core/mcp_connectors.py` inside the `CalendarConnector` class:

```python
def call_tool(self, tool_name: str, arguments: dict) -> list | dict | None:
    """Call any MCP tool on the calendar server and return parsed content.

    Returns None if the MCP library is missing or no endpoint is configured.
    """
    if not MCP_AVAILABLE:
        logger.warning("MCP library not available. call_tool(%s) skipped.", tool_name)
        return None

    if not self.endpoint:
        logger.info("Calendar MCP endpoint not configured. call_tool(%s) skipped.", tool_name)
        return None

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self._call_tool_async(tool_name, arguments))
    except Exception as exc:
        logger.warning("call_tool(%s) failed: %s", tool_name, exc)
        return None
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)

async def _call_tool_async(self, tool_name: str, arguments: dict) -> list | dict | None:
    server_params = self._build_server_parameters()
    session_group = ClientSessionGroup()
    async with session_group:
        session = await session_group.connect_to_server(server_params)
        result = await session.call_tool(tool_name, arguments)

        if result.isError:
            message = self._summarize_error(result)
            raise RuntimeError(f"MCP tool '{tool_name}' error: {message}")

        # Extract text content from MCP response
        text_parts = []
        for chunk in result.content:
            if hasattr(chunk, "text") and chunk.text:
                text_parts.append(chunk.text)

        combined = "\n".join(text_parts)
        # Try to parse as JSON (most MCP tools return JSON)
        import json
        try:
            return json.loads(combined)
        except (json.JSONDecodeError, TypeError):
            return combined or None

def list_events(
    self,
    time_min: str | None = None,
    time_max: str | None = None,
    calendar_id: str = "primary",
    max_results: int = 50,
) -> list:
    """List calendar events in a time range. Returns list of event dicts."""
    args = {"calendarId": calendar_id, "maxResults": max_results}
    if time_min:
        args["timeMin"] = time_min
    if time_max:
        args["timeMax"] = time_max
    result = self.call_tool("list-events", args)
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("items", result.get("events", []))
    return []

def search_events(self, query: str, calendar_id: str = "primary") -> list:
    """Search calendar events by text query."""
    result = self.call_tool("search-events", {
        "calendarId": calendar_id,
        "query": query,
    })
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return result.get("items", result.get("events", []))
    return []
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_mcp_connectors.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add core/mcp_connectors.py tests/test_mcp_connectors.py
git commit -m "feat: add call_tool, list_events, search_events to CalendarConnector"
```

---

## Task 4: Add Availability Checking to SchedulerAgent

**Files:**
- Modify: `agents/scheduler_agent.py`
- Modify: `tests/test_scheduler_agent.py`

**Step 1: Write failing test for availability checking**

Add to `tests/test_scheduler_agent.py`:

```python
class FakeCalendarConnector:
    """In-memory fake for testing calendar interactions."""

    def __init__(self, existing_events=None):
        self.existing_events = existing_events or []
        self.created_events = []

    def create_event(self, payload):
        self.created_events.append(payload)

    def list_events(self, time_min=None, time_max=None, calendar_id="primary", max_results=50):
        return self.existing_events

    def call_tool(self, tool_name, arguments):
        return None


def test_check_availability_finds_conflicts():
    """SchedulerAgent.check_availability returns overlapping events."""
    existing = [
        {"summary": "Team Meeting", "start": {"dateTime": "2026-02-14T17:00:00"}, "end": {"dateTime": "2026-02-14T18:00:00"}},
    ]
    connector = FakeCalendarConnector(existing_events=existing)
    agent = SchedulerAgent(
        llm=DummyLLM('{"start_time": "17:00", "end_time": "19:00", "subjects": ["Math"]}'),
        calendar_connector=connector,
    )
    conflicts = agent.check_availability("2026-02-14", "17:00", "19:00")
    assert len(conflicts) == 1
    assert conflicts[0]["summary"] == "Team Meeting"


def test_check_availability_returns_empty_when_free():
    connector = FakeCalendarConnector(existing_events=[])
    agent = SchedulerAgent(
        llm=DummyLLM('{"start_time":"10:00","end_time":"12:00","subjects":["Math"]}'),
        calendar_connector=connector,
    )
    conflicts = agent.check_availability("2026-02-14", "10:00", "12:00")
    assert conflicts == []


def test_check_availability_none_connector():
    """No connector configured returns empty (graceful degradation)."""
    agent = SchedulerAgent(llm=DummyLLM('{}'), calendar_connector=None)
    conflicts = agent.check_availability("2026-02-14", "10:00", "12:00")
    assert conflicts == []
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_scheduler_agent.py::test_check_availability_finds_conflicts -v
```

Expected: FAIL (`AttributeError: 'SchedulerAgent' object has no attribute 'check_availability'`).

**Step 3: Implement `check_availability` on SchedulerAgent**

Add to `agents/scheduler_agent.py` inside the `SchedulerAgent` class (after `sync_schedule`):

```python
def check_availability(self, date: str, start_time: str, end_time: str) -> list[dict]:
    """Check Google Calendar for conflicts in the given time window.

    Args:
        date: ISO date string "YYYY-MM-DD"
        start_time: "HH:MM" 24-hour format
        end_time: "HH:MM" 24-hour format

    Returns:
        List of conflicting event dicts. Empty list if free or no connector.
    """
    if self.calendar_connector is None:
        return []

    if not hasattr(self.calendar_connector, "list_events"):
        return []

    try:
        window_start = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        window_end = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return []

    try:
        events = self.calendar_connector.list_events(
            time_min=window_start.isoformat(),
            time_max=window_end.isoformat(),
        )
    except Exception as exc:
        logger.warning("Availability check failed: %s", exc)
        return []

    # Filter to events that actually overlap with our window
    conflicts = []
    for event in events:
        event_start_str = event.get("start", {}).get("dateTime") or event.get("start", "")
        event_end_str = event.get("end", {}).get("dateTime") or event.get("end", "")
        if not event_start_str or not event_end_str:
            continue
        try:
            # Handle both ISO formats (with and without timezone)
            event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00")).replace(tzinfo=None)
            event_end = datetime.fromisoformat(event_end_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError):
            continue

        # Overlap: event_start < window_end AND event_end > window_start
        if event_start < window_end and event_end > window_start:
            conflicts.append(event)

    return conflicts
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_scheduler_agent.py -v
```

Expected: all pass including the new `test_check_availability_*` tests.

**Step 5: Commit**

```bash
git add agents/scheduler_agent.py tests/test_scheduler_agent.py
git commit -m "feat: add check_availability to SchedulerAgent"
```

---

## Task 5: Wire Availability Check into the Scheduler Workflow Node

**Files:**
- Modify: `core/workflow_nodes.py` (the `scheduler_agent_node` function)

**Step 1: Add availability check before schedule generation**

In `core/workflow_nodes.py`, inside `scheduler_agent_node`, after the `SchedulerAgent` is created and before `scheduler.generate_schedule(...)` is called (~line 544), add availability checking:

```python
    # === CHECK CALENDAR AVAILABILITY (if configured) ===
    # Try to warn the user about conflicts before generating a schedule
    conflict_warning = ""
    try:
        # Extract date and time from what we know
        # We'll do a quick pre-check; the full schedule uses LLM parsing
        import re as _re
        time_pattern = _re.compile(
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|to)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
            _re.IGNORECASE,
        )
        time_match = time_pattern.search(user_input)
        date_str = None
        # Attempt to extract date from context or preferences
        if "date" in context:
            date_str = context["date"]

        if time_match and date_str and hasattr(calendar_connector, "list_events"):
            start_hh = time_match.group(1)
            start_mm = time_match.group(2) or "00"
            end_hh = time_match.group(4)
            end_mm = time_match.group(5) or "00"
            conflicts = scheduler.check_availability(
                date_str, f"{int(start_hh):02d}:{start_mm}", f"{int(end_hh):02d}:{end_mm}"
            )
            if conflicts:
                names = [c.get("summary", "Event") for c in conflicts[:3]]
                conflict_warning = (
                    f"\n\n> **Heads up:** You have {len(conflicts)} existing event(s) in this window: "
                    f"{', '.join(names)}. Consider adjusting your time.\n"
                )
    except Exception as exc:
        logger.debug("Availability pre-check failed (non-critical): %s", exc)
```

Then prepend `conflict_warning` to the response string (after `response = f"..."` line):

```python
        response = f"📚 I've created your study schedule!\n\n"
        if conflict_warning:
            response += conflict_warning + "\n"
```

**Step 2: Commit**

```bash
git add core/workflow_nodes.py
git commit -m "feat: check calendar availability before generating schedule"
```

---

## Task 6: Update the `update_event` Stub and Add `delete_event`

**Files:**
- Modify: `core/mcp_connectors.py`

**Step 1: Replace the stub `update_event` and add `delete_event`**

Replace the existing stub at the bottom of `CalendarConnector`:

```python
def update_event(self, event_id: str, payload: dict) -> None:
    """Update an existing calendar event via MCP."""
    payload["eventId"] = event_id
    self.call_tool("update-event", payload)

def delete_event(self, event_id: str, calendar_id: str = "primary") -> None:
    """Delete a calendar event via MCP."""
    self.call_tool("delete-event", {
        "calendarId": calendar_id,
        "eventId": event_id,
    })
```

**Step 2: Commit**

```bash
git add core/mcp_connectors.py
git commit -m "feat: implement update_event and delete_event via MCP"
```

---

## Task 7: Google Cloud OAuth Setup Documentation

**Files:**
- Create: `calendar-mcp/SETUP.md`

**Step 1: Write the setup guide**

```markdown
# Google Calendar MCP — OAuth Setup

## Prerequisites

- Google Cloud account
- A Google Cloud project

## Steps

### 1. Enable Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project (or create one)
3. Navigate to **APIs & Services > Library**
4. Search for "Google Calendar API" and **Enable** it

### 2. Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Desktop app** as the application type
4. Download the JSON file

### 3. Place Credentials

```bash
mkdir -p calendar-mcp/credentials
# Copy your downloaded JSON as:
cp ~/Downloads/client_secret_*.json calendar-mcp/credentials/gcp-oauth.keys.json
```

### 4. Add to `.env`

```env
GOOGLE_CALENDAR_MCP_ENABLED=1
```

### 5. First-Time Auth

On first run, the MCP server will open a browser window for Google OAuth consent.
After authorizing, tokens are stored in `calendar-mcp/credentials/` and auto-refresh.

### 6. Add Test User (if app is in test mode)

1. Go to **APIs & Services > OAuth consent screen > Audience**
2. Add your email as a test user
3. Wait 2-3 minutes for propagation

### Notes

- Tokens expire weekly in test mode; re-authenticate when needed
- For production, publish the OAuth consent screen
```

**Step 2: Add `credentials/` to `.gitignore`**

Append to the project `.gitignore`:

```
# Google Calendar MCP credentials (OAuth tokens, secrets)
calendar-mcp/credentials/
```

**Step 3: Commit**

```bash
git add calendar-mcp/SETUP.md .gitignore
git commit -m "docs: add Google Calendar MCP OAuth setup guide"
```

---

## Task 8: Integration Smoke Test

**Files:**
- Create: `tests/test_calendar_integration.py`

**Step 1: Write an integration test that validates the full flow (mock MCP)**

```python
"""Integration test: SchedulerAgent → CalendarConnector → MCP (mocked)."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from agents.scheduler_agent import SchedulerAgent


class MockCalendarConnector:
    """Simulates CalendarConnector for integration testing."""

    def __init__(self):
        self.created_events = []
        self.listed_time_ranges = []

    def create_event(self, payload):
        self.created_events.append(payload)

    def list_events(self, time_min=None, time_max=None, **kwargs):
        self.listed_time_ranges.append((time_min, time_max))
        return []  # No conflicts

    def call_tool(self, tool_name, arguments):
        return None


class DummyLLM:
    def generate(self, prompt):
        return '{"start_time": "14:00", "end_time": "16:00", "subjects": ["Python"], "date": "2026-02-14"}'


def test_full_schedule_and_sync_flow():
    """Generate schedule, check availability, sync to calendar."""
    connector = MockCalendarConnector()
    agent = SchedulerAgent(llm=DummyLLM(), calendar_connector=connector)

    # Generate schedule
    schedule = agent.generate_schedule({"user_input": "tomorrow 14:00-16:00 study Python"})
    assert len(schedule["sessions"]) > 0

    # Check availability
    conflicts = agent.check_availability("2026-02-14", "14:00", "16:00")
    assert conflicts == []
    assert len(connector.listed_time_ranges) == 1

    # Sync to calendar
    agent.sync_schedule(schedule)
    study_sessions = [s for s in schedule["sessions"] if s["type"] == "study"]
    assert len(connector.created_events) == len(study_sessions)

    # Verify event payloads
    first_event = connector.created_events[0]
    assert "Study: Python" in first_event["summary"]
    assert first_event["calendarId"] == "primary"


def test_schedule_with_existing_conflicts():
    """When calendar has conflicts, check_availability reports them."""
    connector = MockCalendarConnector()
    connector.list_events = lambda **kw: [
        {
            "summary": "Team Standup",
            "start": {"dateTime": "2026-02-14T14:30:00"},
            "end": {"dateTime": "2026-02-14T15:00:00"},
        }
    ]
    agent = SchedulerAgent(llm=DummyLLM(), calendar_connector=connector)

    conflicts = agent.check_availability("2026-02-14", "14:00", "16:00")
    assert len(conflicts) == 1
    assert conflicts[0]["summary"] == "Team Standup"
```

**Step 2: Run the integration test**

```bash
pytest tests/test_calendar_integration.py -v
```

Expected: PASS.

**Step 3: Commit**

```bash
git add tests/test_calendar_integration.py
git commit -m "test: add calendar integration smoke tests"
```

---

## Task 9: Run Full Test Suite and Verify

**Step 1: Run all tests**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass, including existing scheduler tests and new calendar tests.

**Step 2: Verify dev startup (optional, manual)**

```bash
GOOGLE_CALENDAR_MCP_ENABLED=1 ./start_dev.sh
```

Check logs:
- `logs/calendar-mcp.log` — MCP server should start on port 3001
- Backend should log `GOOGLE_CALENDAR_MCP_URL=http://localhost:3001/mcp`

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: self-hosted google calendar MCP integration complete"
```

---

## Summary of Changes

| File | Action | Purpose |
|------|--------|---------|
| `calendar-mcp/Dockerfile` | Create | Docker image for nspady/google-calendar-mcp |
| `calendar-mcp/.env.example` | Create | OAuth credential template |
| `calendar-mcp/SETUP.md` | Create | OAuth setup documentation |
| `docker-compose.yml` | Modify | Add calendar-mcp sidecar service |
| `start_dev.sh` | Modify | Optional local MCP server startup |
| `core/mcp_connectors.py` | Modify | Add `call_tool`, `list_events`, `search_events`, implement `update_event`, `delete_event` |
| `agents/scheduler_agent.py` | Modify | Add `check_availability` method |
| `core/workflow_nodes.py` | Modify | Pre-check calendar availability before scheduling |
| `tests/test_mcp_connectors.py` | Create | Unit tests for CalendarConnector |
| `tests/test_scheduler_agent.py` | Modify | Tests for availability checking |
| `tests/test_calendar_integration.py` | Create | Integration smoke tests |
| `.gitignore` | Modify | Exclude OAuth credentials |

## MCP Tools Available After Integration

| Tool | Method on CalendarConnector | Used By |
|------|----------------------------|---------|
| `create-event` | `create_event(payload)` | `SchedulerAgent.sync_schedule()` |
| `list-events` | `list_events(time_min, time_max)` | `SchedulerAgent.check_availability()` |
| `search-events` | `search_events(query)` | Future: find study sessions |
| `update-event` | `update_event(event_id, payload)` | Future: reschedule sessions |
| `delete-event` | `delete_event(event_id)` | Future: cancel sessions |
| `list-calendars` | `call_tool("list-calendars", {})` | Future: multi-calendar support |

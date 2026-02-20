"""Integration test: SchedulerAgent -> GoogleCalendarClient (mocked)."""

from __future__ import annotations

from agents.scheduler_agent import SchedulerAgent


class MockGoogleCalendarClient:
    """Simulates GoogleCalendarClient for integration testing."""

    def __init__(self):
        self.created_events = []
        self.listed_time_ranges = []

    def create_event(self, payload):
        self.created_events.append(payload)

    def list_events(self, time_min=None, time_max=None, **kwargs):
        self.listed_time_ranges.append((time_min, time_max))
        return []  # No conflicts

    def search_events(self, query, calendar_id="primary"):
        return []

    def update_event(self, event_id, payload):
        pass

    def delete_event(self, event_id, calendar_id="primary"):
        pass


class DummyLLM:
    def generate(self, prompt):
        return '{"start_time": "14:00", "end_time": "16:00", "subjects": ["Python"], "date": "2026-02-14"}'


def test_full_schedule_and_sync_flow():
    """Generate schedule, check availability, sync to Google Calendar."""
    connector = MockGoogleCalendarClient()
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

    # Verify event payloads (Google Calendar API format)
    first_event = connector.created_events[0]
    assert "Study: Python" in first_event["summary"]
    assert "dateTime" in first_event["start"]
    assert first_event["start"]["timeZone"] == "Asia/Jerusalem"


def test_schedule_with_existing_conflicts():
    """When calendar has conflicts, check_availability reports them."""
    connector = MockGoogleCalendarClient()
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

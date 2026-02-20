"""Tests for the SchedulerAgent Pomodoro planning workflow."""

from __future__ import annotations

import pytest

from agents.scheduler_agent import SchedulerAgent


class DummyLLM:
    """Returns a canned JSON response for deterministic testing."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def make_agent(json_response: str) -> SchedulerAgent:
    """Helper to build a scheduler agent with a canned LLM reply."""
    return SchedulerAgent(llm=DummyLLM(json_response))


def test_generate_schedule_creates_rotating_pomodoro_blocks() -> None:
    agent = make_agent('{"start_time": "17:00", "end_time": "19:00", "subjects": ["Math", "Physics"], "notes": ""}')

    schedule = agent.generate_schedule({"user_input": "I am free after 5pm until 7pm for math and physics."})

    sessions = schedule["sessions"]
    # 17:00-19:00 allows four study blocks and four short breaks.
    assert len(sessions) == 8
    assert sessions[0]["type"] == "study"
    assert sessions[0]["subject"] == "Math"
    assert sessions[0]["start"] == "17:00"
    assert sessions[0]["end"] == "17:25"

    assert sessions[1]["type"] == "break"
    assert sessions[1]["start"] == "17:25"
    assert sessions[1]["end"] == "17:30"

    # Rotation picks Physics for the second study block.
    assert sessions[2]["type"] == "study"
    assert sessions[2]["subject"] == "Physics"

    # Final entry is the closing break (18:55-19:00).
    assert sessions[-1]["type"] == "break"
    assert sessions[-1]["start"] == "18:55"
    assert sessions[-1]["end"] == "19:00"

    assert schedule["preferences"]["start_time"] == "17:00"
    assert "subjects" in schedule["preferences"]


def test_generate_schedule_requires_user_input() -> None:
    agent = make_agent('{"start_time": "09:00", "end_time": "10:00", "subjects": ["Math"]}')
    with pytest.raises(ValueError, match="Context must include 'user_input'"):
        agent.generate_schedule({})


def test_invalid_json_from_llm_raises() -> None:
    agent = make_agent("not valid json")
    with pytest.raises(ValueError, match="valid JSON"):
        agent.generate_schedule({"user_input": "study time"})


def test_missing_required_fields_raises() -> None:
    agent = make_agent('{"start_time": "08:00"}')
    with pytest.raises(ValueError, match="missing fields"):
        agent.generate_schedule({"user_input": "morning study"})


def test_end_before_start_raises() -> None:
    agent = make_agent('{"start_time": "12:00", "end_time": "11:00", "subjects": ["History"]}')
    with pytest.raises(ValueError, match="End time must be after start time"):
        agent.generate_schedule({"user_input": "lunch study"})


def test_window_too_small_for_pomodoro_raises() -> None:
    agent = SchedulerAgent(
        llm=DummyLLM('{"start_time": "10:00", "end_time": "10:10", "subjects": ["Biology"]}'),
        pomodoro_minutes=25,
        break_minutes=5,
    )
    with pytest.raises(ValueError, match="No Pomodoro blocks fit"):
        agent.generate_schedule({"user_input": "short break"})


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
        {
            "summary": "Team Meeting",
            "start": {"dateTime": "2026-02-14T17:00:00"},
            "end": {"dateTime": "2026-02-14T18:00:00"},
        },
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
    agent = SchedulerAgent(llm=DummyLLM("{}"), calendar_connector=None)
    conflicts = agent.check_availability("2026-02-14", "10:00", "12:00")
    assert conflicts == []


def test_invalid_time_format_raises() -> None:
    agent = make_agent('{"start_time": "10AM", "end_time": "12:00", "subjects": ["Chemistry"]}')
    with pytest.raises(ValueError, match="HH:MM 24-hour"):
        agent.generate_schedule({"user_input": "late morning study"})

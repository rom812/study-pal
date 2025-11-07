"""Scheduler agent gathers availability and builds Pomodoro study plans."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from core.weakness_analyzer import SessionRecommendations

try:  # pragma: no cover - import guard for environments without OpenAI installed
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


class ConversationModel(Protocol):
    """Minimal LLM interface used by the scheduler agent."""

    def generate(self, prompt: str) -> str:
        ...


DEFAULT_POMODORO_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5


@dataclass
class SchedulerAgent:
    """Collects user study preferences and produces a Pomodoro schedule."""

    llm: ConversationModel | None = None
    pomodoro_minutes: int = DEFAULT_POMODORO_MINUTES
    break_minutes: int = DEFAULT_BREAK_MINUTES
    calendar_connector: object | None = None

    _last_schedule: dict | None = field(default=None, init=False, repr=False)

    def generate_schedule(
        self,
        context: dict,
        recommendations: SessionRecommendations | None = None,
    ) -> dict:
        """
        Create a schedule from conversational context, optionally prioritizing weak points.

        Args:
            context: Dictionary containing user_input with availability and subjects
            recommendations: Optional SessionRecommendations from tutor analysis to prioritize weak topics

        Returns:
            Schedule dictionary with preferences and sessions
        """
        user_input = context.get("user_input") or context.get("preferences_text")
        if not user_input:
            raise ValueError("Context must include 'user_input' describing availability and subjects.")

        llm = self._ensure_llm()
        preferences = self._collect_preferences(user_input, llm)

        # If we have recommendations, adjust the subject prioritization
        if recommendations and recommendations.weak_points:
            preferences = self._prioritize_weak_topics(preferences, recommendations)

        sessions = self._build_pomodoro_plan(preferences)

        # Add metadata about weak points if available
        schedule = {
            "preferences": preferences,
            "sessions": sessions,
            "based_on_weak_points": recommendations is not None and len(recommendations.weak_points) > 0,
        }

        self._last_schedule = schedule
        return schedule

    def sync_schedule(self, schedule: dict) -> None:
        """Persist the latest schedule by creating calendar events."""
        self._last_schedule = schedule

        if self.calendar_connector is None:
            return  # No calendar integration configured

        # Create calendar events for each study block
        sessions = schedule.get("sessions", [])
        preferences = schedule.get("preferences", {})

        for session in sessions:
            if session.get("type") != "study":
                continue  # Only create events for study blocks, not breaks

            # Build the calendar event payload
            payload = self._build_calendar_event_payload(session, preferences)

            try:
                self.calendar_connector.create_event(payload)
            except Exception as exc:
                # Log but don't fail the entire sync if one event fails
                print(f"Failed to create calendar event: {exc}")

    def _build_calendar_event_payload(self, session: dict, preferences: dict) -> dict:
        """Build a calendar event payload for a study session."""
        from datetime import datetime, timedelta

        # Parse start and end times
        start_time_str = session["start"]  # Format: "HH:MM"
        end_time_str = session["end"]
        subject = session.get("subject", "Study")

        # Convert to ISO 8601 datetime strings (assuming today's date)
        today = datetime.now().date()
        start_dt = datetime.combine(today, datetime.strptime(start_time_str, "%H:%M").time())
        end_dt = datetime.combine(today, datetime.strptime(end_time_str, "%H:%M").time())

        # Build the MCP create_event payload
        # Format: https://github.com/nspady/google-calendar-mcp
        return {
            "calendarId": "primary",  # Use primary calendar
            "summary": f"Study: {subject}",
            "description": f"Pomodoro study session for {subject}",
            "start": start_dt.isoformat(),  # ISO 8601 string
            "end": end_dt.isoformat(),  # ISO 8601 string
            "timeZone": "Asia/Jerusalem",  # Israel timezone
        }

    def _ensure_llm(self) -> ConversationModel:
        if self.llm is None:
            self.llm = OpenAIConversationModel()
        return self.llm

    def _collect_preferences(self, user_input: str, llm: ConversationModel) -> dict:
        prompt = (
            "You are Study Pal's scheduling assistant.\n"
            "Extract the user's study availability and subjects from the note below and respond ONLY with JSON.\n"
            "Required keys: start_time (HH:MM 24-hour), end_time (HH:MM 24-hour), subjects (array of strings).\n"
            "Optional key: notes (string) for assumptions or clarifications.\n"
            f"USER_NOTE: {user_input}\n"
        )
        raw_response = llm.generate(prompt)
        preferences = self._parse_preferences(raw_response)
        preferences.setdefault("notes", "")
        return preferences

    def _parse_preferences(self, raw: str) -> dict:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Scheduler LLM must return valid JSON.") from exc

        required = {"start_time", "end_time", "subjects"}
        missing = [key for key in required if key not in parsed]
        if missing:
            raise ValueError(f"Scheduler LLM response missing fields: {', '.join(missing)}")

        subjects = parsed["subjects"]
        if not isinstance(subjects, list) or not subjects:
            raise ValueError("Scheduler LLM must return a non-empty 'subjects' list.")
        if not all(isinstance(item, str) and item.strip() for item in subjects):
            raise ValueError("Each subject must be a non-empty string.")

        return parsed

    def _build_pomodoro_plan(self, preferences: dict) -> list[dict]:
        start = self._parse_clock(preferences["start_time"])
        end = self._parse_clock(preferences["end_time"])
        if end <= start:
            raise ValueError("End time must be after start time.")

        pomodoro_delta = timedelta(minutes=self.pomodoro_minutes)
        break_delta = timedelta(minutes=self.break_minutes)
        sessions: list[dict] = []

        subjects = preferences["subjects"]
        subject_index = 0
        current = start

        while current + pomodoro_delta <= end:
            block_end = current + pomodoro_delta
            subject = subjects[subject_index % len(subjects)]
            sessions.append(
                {
                    "type": "study",
                    "subject": subject,
                    "start": current.strftime("%H:%M"),
                    "end": block_end.strftime("%H:%M"),
                }
            )
            current = block_end

            if current + break_delta > end:
                break

            break_end = current + break_delta
            sessions.append(
                {
                    "type": "break",
                    "start": current.strftime("%H:%M"),
                    "end": break_end.strftime("%H:%M"),
                }
            )
            current = break_end
            subject_index += 1

        if not sessions:
            raise ValueError("No Pomodoro blocks fit within the provided availability window.")

        return sessions

    def _prioritize_weak_topics(
        self,
        preferences: dict,
        recommendations: SessionRecommendations,
    ) -> dict:
        """
        Adjust subject prioritization based on weak points from tutoring session.

        Args:
            preferences: Original preferences from user input
            recommendations: SessionRecommendations with weak_points

        Returns:
            Modified preferences with prioritized subjects
        """
        original_subjects = preferences.get("subjects", [])
        weak_topics = [wp.topic for wp in recommendations.weak_points]

        # Build prioritized subject list
        prioritized_subjects = []

        # 1. Add severe difficulty topics first
        severe_topics = [
            wp.topic
            for wp in recommendations.weak_points
            if wp.difficulty_level == "severe"
        ]
        for topic in severe_topics:
            if topic not in prioritized_subjects:
                prioritized_subjects.append(topic)

        # 2. Add moderate difficulty topics
        moderate_topics = [
            wp.topic
            for wp in recommendations.weak_points
            if wp.difficulty_level == "moderate"
        ]
        for topic in moderate_topics:
            if topic not in prioritized_subjects:
                prioritized_subjects.append(topic)

        # 3. Add mild difficulty topics
        mild_topics = [
            wp.topic
            for wp in recommendations.weak_points
            if wp.difficulty_level == "mild"
        ]
        for topic in mild_topics:
            if topic not in prioritized_subjects:
                prioritized_subjects.append(topic)

        # 4. Add remaining subjects from user input
        for subject in original_subjects:
            if subject not in prioritized_subjects:
                prioritized_subjects.append(subject)

        # Update preferences
        preferences["subjects"] = prioritized_subjects if prioritized_subjects else original_subjects
        preferences["weak_points_prioritized"] = True
        preferences["severe_topics"] = severe_topics
        preferences["moderate_topics"] = moderate_topics

        return preferences

    def _parse_clock(self, value: str) -> datetime:
        try:
            time_obj = datetime.strptime(value, "%H:%M").time()
        except ValueError as exc:
            raise ValueError("Times must be provided in HH:MM 24-hour format.") from exc

        today = datetime.now()
        return datetime.combine(today.date(), time_obj)


class OpenAIConversationModel:
    """Chat completion wrapper using OpenAI's API."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        system_prompt: str | None = None,
    ) -> None:
        if OpenAI is None:  # pragma: no cover - import defender
            raise ImportError(
                "The 'openai' package is required to use OpenAIConversationModel. "
                "Install it via `pip install openai`."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set. "
                "Provide an API key to enable the scheduler agent."
            )

        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.system_prompt = (
            system_prompt
            or "You help Study Pal students plan productive Pomodoro study sessions. Respond with JSON only."
        )

    def generate(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        choice = response.choices[0].message
        content = choice.content

        if isinstance(content, str):
            text = content
        else:
            text = "".join(getattr(part, "text", "") for part in content)

        if not text.strip():
            raise RuntimeError("OpenAI returned an empty response for the scheduling prompt.")

        return text.strip()

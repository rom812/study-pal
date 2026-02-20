"""Scheduler agent gathers availability and builds Pomodoro study plans."""

from __future__ import annotations

import json
import logging
import os
import re
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

    def generate(self, prompt: str) -> str: ...


DEFAULT_POMODORO_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
DEFAULT_START_TIME = "09:00"

logger = logging.getLogger(__name__)


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
        recommendations: "SessionRecommendations | dict | None" = None,
    ) -> dict:
        """
        Create a schedule from conversational context, optionally prioritizing weak points.

        Args:
            context: Dictionary containing user_input with availability and subjects
            recommendations: Optional SessionRecommendations or dict from tutor analysis to prioritize weak topics

        Returns:
            Schedule dictionary with preferences and sessions
        """
        user_input = context.get("user_input") or context.get("preferences_text")
        if not user_input:
            raise ValueError("Context must include 'user_input' describing availability and subjects.")

        llm = self._ensure_llm()
        preferences = self._collect_preferences(user_input, llm, context)

        # Convert dict to SessionRecommendations if needed
        if isinstance(recommendations, dict):
            recommendations = self._dict_to_recommendations(recommendations)

        # If we have recommendations, adjust the subject prioritization
        if recommendations and hasattr(recommendations, "weak_points") and recommendations.weak_points:
            preferences = self._prioritize_weak_topics(preferences, recommendations)

        sessions = self._build_pomodoro_plan(preferences)

        # Add metadata about weak points if available
        schedule = {
            "preferences": preferences,
            "sessions": sessions,
            "based_on_weak_points": recommendations is not None
            and (hasattr(recommendations, "weak_points") and len(recommendations.weak_points) > 0),
        }

        self._last_schedule = schedule
        return schedule

    def _dict_to_recommendations(self, data: dict) -> "SessionRecommendations":
        """Convert a dict (from LangGraph state) to SessionRecommendations object."""
        from core.weakness_analyzer import SessionRecommendations

        # Use the from_dict class method for conversion
        return SessionRecommendations.from_dict(data)

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
        from datetime import datetime

        subject = session.get("subject", "Study")

        # Prefer full ISO datetime strings from the session (already include correct date)
        start_iso = session.get("start_datetime")
        end_iso = session.get("end_datetime")

        if start_iso and end_iso:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = datetime.fromisoformat(end_iso)
        else:
            # Fallback: combine session date (or preference date, or today) with times
            start_time_str = session["start"]  # Format: "HH:MM"
            end_time_str = session["end"]

            session_date = session.get("date") or preferences.get("date")
            if session_date:
                try:
                    date_obj = datetime.strptime(session_date, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    date_obj = datetime.now().date()
            else:
                date_obj = datetime.now().date()

            start_dt = datetime.combine(date_obj, datetime.strptime(start_time_str, "%H:%M").time())
            end_dt = datetime.combine(date_obj, datetime.strptime(end_time_str, "%H:%M").time())

        # Google Calendar API event format
        return {
            "summary": f"Study: {subject}",
            "description": f"Pomodoro study session for {subject}",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Jerusalem"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Jerusalem"},
        }

    def _ensure_llm(self) -> ConversationModel | None:
        if self.llm is not None:
            return self.llm

        try:
            self.llm = OpenAIConversationModel()
        except Exception as exc:  # pragma: no cover - runtime fallback
            logger.warning(
                "OpenAIConversationModel unavailable (%s). Falling back to heuristic scheduler.",
                exc,
            )
            self.llm = None
        return self.llm

    def _collect_preferences(
        self,
        user_input: str,
        llm: ConversationModel | None,
        context: dict | None,
    ) -> dict:
        current_date = datetime.now()
        prompt = (
            "You are Study Pal's scheduling assistant.\n"
            "Extract the user's study availability and subjects from the note below and respond ONLY with JSON.\n"
            "Required keys: start_time (HH:MM 24-hour), end_time (HH:MM 24-hour), subjects (array of strings).\n"
            "Required keys (ALWAYS include):\n"
            "  - date (YYYY-MM-DD format): The specific date for the session. You MUST calculate and include this.\n"
            "    * If user says 'today' → use today's date\n"
            "    * If user says 'tomorrow' → use tomorrow's date\n"
            f"    * If user says a day of week (e.g. 'Tuesday') → calculate the NEXT occurrence from today ({current_date.strftime('%A, %Y-%m-%d')})\n"
            "    * If no day specified → default to today's date\n"
            "Optional keys:\n"
            "  - notes (string): Any assumptions or clarifications.\n"
            f"IMPORTANT: Today is {current_date.strftime('%A, %B %d, %Y')} ({current_date.strftime('%Y-%m-%d')}). "
            f"Current day of week: {current_date.strftime('%A')}.\n"
            f"USER_NOTE: {user_input}\n"
        )
        if llm is None:
            preferences = self._heuristic_preferences(user_input, context)
        else:
            try:
                raw_response = llm.generate(prompt)
                preferences = self._parse_preferences(raw_response)
            except Exception as exc:  # pragma: no cover - runtime fallback
                logger.warning(
                    "Scheduler LLM response failed (%s). Using heuristic fallback.",
                    exc,
                )
                preferences = self._heuristic_preferences(user_input, context)
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
        session_date = preferences.get("date")
        start = self._parse_clock(preferences["start_time"], base_date=session_date)
        end = self._parse_clock(preferences["end_time"], base_date=session_date)

        if end <= start:
            raise ValueError("End time must be after start time.")

        pomodoro_delta = timedelta(minutes=self.pomodoro_minutes)
        break_delta = timedelta(minutes=self.break_minutes)
        sessions: list[dict] = []

        subjects = preferences["subjects"]
        subject_index = 0
        current = start
        session_count_per_subject = {}  # Track how many sessions per subject

        # Fill the entire time window with sessions
        while current < end:
            # Check if we can fit a full Pomodoro block
            if current + pomodoro_delta <= end:
                block_end = current + pomodoro_delta
                subject = subjects[subject_index % len(subjects)]

                # Track session count
                session_count_per_subject[subject] = session_count_per_subject.get(subject, 0) + 1
                session_num = session_count_per_subject[subject]

                # Add variety to task descriptions
                task_description = self._generate_task_description(subject, session_num)

                sessions.append(
                    {
                        "type": "study",
                        "subject": subject,
                        "task": task_description,
                        "start": current.strftime("%H:%M"),
                        "end": block_end.strftime("%H:%M"),
                        "start_datetime": current.isoformat(),
                        "end_datetime": block_end.isoformat(),
                        "date": current.strftime("%Y-%m-%d"),
                        "day_name": current.strftime("%A"),
                    }
                )
                current = block_end

                # Add break if there's room
                if current + break_delta <= end:
                    break_end = current + break_delta
                    sessions.append(
                        {
                            "type": "break",
                            "start": current.strftime("%H:%M"),
                            "end": break_end.strftime("%H:%M"),
                            "start_datetime": current.isoformat(),
                            "end_datetime": break_end.isoformat(),
                            "date": current.strftime("%Y-%m-%d"),
                            "day_name": current.strftime("%A"),
                        }
                    )
                    current = break_end
                    subject_index += 1
                else:
                    # Not enough room for a break, but continue to fill window
                    break
            else:
                # Not enough time for a full Pomodoro, but we have time left
                # Create a shorter study session to fill the remaining time
                remaining_minutes = int((end - current).total_seconds() / 60)
                if remaining_minutes >= 10:  # Only add if at least 10 minutes remain
                    subject = subjects[subject_index % len(subjects)]
                    session_count_per_subject[subject] = session_count_per_subject.get(subject, 0) + 1
                    session_num = session_count_per_subject[subject]
                    task_description = self._generate_task_description(subject, session_num)

                    sessions.append(
                        {
                            "type": "study",
                            "subject": subject,
                            "task": task_description,
                            "start": current.strftime("%H:%M"),
                            "end": end.strftime("%H:%M"),
                            "start_datetime": current.isoformat(),
                            "end_datetime": end.isoformat(),
                            "date": current.strftime("%Y-%m-%d"),
                            "day_name": current.strftime("%A"),
                            "duration_note": f"{remaining_minutes} min session",
                        }
                    )
                break

        if not sessions:
            raise ValueError("No Pomodoro blocks fit within the provided availability window.")

        return sessions

    def _generate_task_description(self, subject: str, session_number: int) -> str:
        """Generate varied task descriptions based on subject and session number."""
        task_templates = [
            "Learn core concepts",
            "Practice exercises",
            "Review and reinforce",
            "Work on problem sets",
            "Deep dive practice",
            "Master fundamentals",
            "Apply concepts",
            "Quiz yourself",
        ]

        # Cycle through different task types
        template = task_templates[(session_number - 1) % len(task_templates)]
        return f"{template} - {subject}"

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
        severe_topics = [wp.topic for wp in recommendations.weak_points if wp.difficulty_level == "severe"]
        for topic in severe_topics:
            if topic not in prioritized_subjects:
                prioritized_subjects.append(topic)

        # 2. Add moderate difficulty topics
        moderate_topics = [wp.topic for wp in recommendations.weak_points if wp.difficulty_level == "moderate"]
        for topic in moderate_topics:
            if topic not in prioritized_subjects:
                prioritized_subjects.append(topic)

        # 3. Add mild difficulty topics
        mild_topics = [wp.topic for wp in recommendations.weak_points if wp.difficulty_level == "mild"]
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

    def _heuristic_preferences(self, user_input: str, context: dict | None) -> dict:
        start_time, end_time = self._extract_time_range(user_input)
        subjects = self._extract_subjects(user_input)
        session_date = self._extract_date(user_input)

        if context:
            topic = context.get("topic")
            if topic and topic not in subjects:
                subjects.append(topic)

        if not subjects:
            subjects = ["General Study"]

        start_time = start_time or DEFAULT_START_TIME
        end_time = end_time or self._add_minutes(start_time, 60)

        if self._time_to_minutes(end_time) <= self._time_to_minutes(start_time):
            end_time = self._add_minutes(start_time, 60)

        result = {
            "start_time": start_time,
            "end_time": end_time,
            "subjects": subjects,
            "notes": "Generated via heuristic parser (LLM unavailable).",
        }

        if session_date:
            result["date"] = session_date

        return result

    def _extract_date(self, text: str) -> str | None:
        """Extract date from user input (today, tomorrow, or day of week)."""
        text_lower = text.lower()
        now = datetime.now()

        # Check for "today"
        if "today" in text_lower:
            return now.strftime("%Y-%m-%d")

        # Check for "tomorrow"
        if "tomorrow" in text_lower:
            return (now + timedelta(days=1)).strftime("%Y-%m-%d")

        # Check for day of week
        days_of_week = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        for day_name, day_num in days_of_week.items():
            if day_name in text_lower:
                # Calculate next occurrence of this day
                current_day = now.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7  # If it's today, schedule for next week
                target_date = now + timedelta(days=days_ahead)
                return target_date.strftime("%Y-%m-%d")

        return None

    def _extract_time_range(self, text: str) -> tuple[str | None, str | None]:
        range_pattern = re.compile(
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*(?:-|to)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?",
            re.IGNORECASE,
        )
        match = range_pattern.search(text)
        if match:
            start = self._format_time(match.group(1), match.group(2), match.group(3), match.group(6))
            end = self._format_time(match.group(4), match.group(5), match.group(6), match.group(3))
            return start, end

        single_pattern = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", re.IGNORECASE)
        times = single_pattern.findall(text)
        if len(times) >= 2:
            start = self._format_time(*times[0])
            end = self._format_time(*times[1])
            return start, end
        if len(times) == 1:
            start = self._format_time(*times[0])
            end = self._add_minutes(start, 60)
            return start, end
        return None, None

    def _format_time(
        self,
        hour: str,
        minute: str | None,
        ampm: str | None,
        fallback_ampm: str | None = None,
    ) -> str:
        hour_val = int(hour)
        minute_val = int(minute or 0)
        marker = (ampm or fallback_ampm or "").lower()

        if marker:
            hour_val = hour_val % 12
            if marker == "pm":
                hour_val += 12
        return f"{hour_val:02d}:{minute_val:02d}"

    def _add_minutes(self, time_str: str, minutes: int) -> str:
        base = datetime.strptime(time_str, "%H:%M")
        updated = base + timedelta(minutes=minutes)
        return updated.strftime("%H:%M")

    def _time_to_minutes(self, time_str: str) -> int:
        hour, minute = map(int, time_str.split(":"))
        return hour * 60 + minute

    def _extract_subjects(self, text: str) -> list[str]:
        chunks: list[str] = []
        markers = [
            r"focus on\s+([^.]+)",
            r"study\s+([^.]+)",
            r"studying\s+([^.]+)",
            r"work on\s+([^.]+)",
            r"review\s+([^.]+)",
            r"subjects?\s*:\s*([^.]+)",
            r"topics?\s*:\s*([^.]+)",
        ]
        for pattern in markers:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                chunks.append(match.group(1))

        subjects: list[str] = []
        seen: set[str] = set()
        for chunk in chunks:
            parts = re.split(r",|/|\band\b|\bthen\b|&", chunk, flags=re.IGNORECASE)
            for part in parts:
                subject = part.strip(" .")
                if not subject:
                    continue
                key = subject.lower()
                if key not in seen:
                    seen.add(key)
                    subjects.append(subject)
        return subjects

    def _parse_clock(self, value: str, base_date: str | None = None) -> datetime:
        try:
            time_obj = datetime.strptime(value, "%H:%M").time()
        except ValueError as exc:
            raise ValueError("Times must be provided in HH:MM 24-hour format.") from exc

        if base_date:
            try:
                date_obj = datetime.strptime(base_date, "%Y-%m-%d").date()
                return datetime.combine(date_obj, time_obj)
            except (ValueError, TypeError):
                pass
        return datetime.combine(datetime.now().date(), time_obj)


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
                "The 'openai' package is required to use OpenAIConversationModel. Install it via `pip install openai`."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set. Provide an API key to enable the scheduler agent."
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

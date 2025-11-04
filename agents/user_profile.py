"""User profile models supporting motivational personalization."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class UserProgressEvent(BaseModel):
    """Record describing a notable study event or milestone."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: Literal["win", "struggle", "burnout", "milestone", "checkpoint", "custom"]
    summary: str
    details: str | None = None
    sentiment: Literal["positive", "neutral", "negative"] | None = None


class UserProfile(BaseModel):
    """Long-lived attributes that guide motivational messaging."""

    user_id: str
    name: str
    primary_persona: str = Field(default="default")
    preferred_personas: list[str] = Field(default_factory=list)
    academic_field: str | None = None
    study_topics: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    traits: list[str] = Field(
        default_factory=list,
        description="Behavioural cues such as procrastination, perfectionism, burnout.",
    )
    progress_log: list[UserProgressEvent] = Field(default_factory=list)
    current_focus: str | None = None
    last_motivation_at: datetime | None = None

    def register_event(self, event: UserProgressEvent) -> None:
        """Append a progress event and keep log bounded."""
        self.progress_log.append(event)
        # Retain only the 50 most recent events to avoid unbounded storage.
        if len(self.progress_log) > 50:
            self.progress_log[:] = self.progress_log[-50:]


class UserProfileStore:
    """Simple JSON backed persistence keyed by user id."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _path_for(self, user_id: str) -> Path:
        safe_id = user_id.replace("/", "_")
        return self.root / f"{safe_id}.json"

    def load(self, user_id: str) -> UserProfile:
        """Load a user profile from disk."""
        path = self._path_for(user_id)
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {path}")
        data = path.read_text(encoding="utf-8")
        return UserProfile.model_validate_json(data)

    def save(self, profile: UserProfile) -> None:
        """Persist a user profile to disk."""
        path = self._path_for(profile.user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

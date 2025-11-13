"""Data structures and utilities for weakness tracking and session analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class WeakPoint:
    """Represents a topic where the user struggled during the session."""

    topic: str
    difficulty_level: Literal["mild", "moderate", "severe"]
    evidence: list[str] = field(default_factory=list)  # Quotes from conversation
    frequency: int = 1  # How many times topic came up
    confusion_indicators: int = 0  # Number of confusion signals detected


@dataclass
class SessionRecommendations:
    """Recommendations generated after analyzing a tutoring session."""

    weak_points: list[WeakPoint]
    priority_topics: list[str]  # Ordered by difficulty
    suggested_focus_time: dict[str, int]  # topic -> minutes
    study_approach_tips: list[str]
    session_summary: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "weak_points": [
                {
                    "topic": wp.topic,
                    "difficulty_level": wp.difficulty_level,
                    "evidence": wp.evidence,
                    "frequency": wp.frequency,
                    "confusion_indicators": wp.confusion_indicators,
                }
                for wp in self.weak_points
            ],
            "priority_topics": self.priority_topics,
            "suggested_focus_time": self.suggested_focus_time,
            "study_approach_tips": self.study_approach_tips,
            "session_summary": self.session_summary,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> SessionRecommendations:
        """
        Create SessionRecommendations from dictionary.

        Args:
            data: Dictionary with recommendation data

        Returns:
            SessionRecommendations object
        """
        # Convert weak_points dicts to WeakPoint objects
        weak_points = []
        for wp_data in data.get("weak_points", []):
            weak_point = WeakPoint(
                topic=wp_data.get("topic", "unknown"),
                difficulty_level=wp_data.get("difficulty_level", "mild"),
                evidence=wp_data.get("evidence", []),
                frequency=wp_data.get("frequency", 1),
                confusion_indicators=wp_data.get("confusion_indicators", 0),
            )
            weak_points.append(weak_point)

        # Handle timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            weak_points=weak_points,
            priority_topics=data.get("priority_topics", []),
            suggested_focus_time=data.get("suggested_focus_time", {}),
            study_approach_tips=data.get("study_approach_tips", []),
            session_summary=data.get("session_summary", ""),
            timestamp=timestamp,
        )

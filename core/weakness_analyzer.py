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

    def __post_init__(self):
        """Calculate difficulty level based on evidence if not explicitly set."""
        if self.frequency >= 5 or self.confusion_indicators >= 3:
            self.difficulty_level = "severe"
        elif self.frequency >= 3 or self.confusion_indicators >= 2:
            self.difficulty_level = "moderate"
        else:
            self.difficulty_level = "mild"


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


class RecommendationBuilder:
    """Helper class to build SessionRecommendations from WeakPoints."""

    @staticmethod
    def calculate_focus_time(weak_points: list[WeakPoint]) -> dict[str, int]:
        """
        Calculate suggested study time for each weak point.

        Args:
            weak_points: List of identified weak points

        Returns:
            Dictionary mapping topic to suggested minutes
        """
        if not weak_points:
            return {}

        focus_time = {}
        severity_weights = {"severe": 30, "moderate": 20, "mild": 10}

        for wp in weak_points:
            base_time = severity_weights.get(wp.difficulty_level, 10)
            # Add extra time based on frequency
            extra_time = min(wp.frequency * 5, 20)
            focus_time[wp.topic] = base_time + extra_time

        return focus_time

    @staticmethod
    def generate_study_tips(weak_points: list[WeakPoint]) -> list[str]:
        """Generate study approach tips based on identified weak points."""
        tips = []

        if not weak_points:
            tips.append("Great session! Continue building on what you learned.")
            return tips

        # Count severity levels
        severe_count = sum(1 for wp in weak_points if wp.difficulty_level == "severe")
        moderate_count = sum(1 for wp in weak_points if wp.difficulty_level == "moderate")

        if severe_count > 0:
            tips.append(
                f"Focus on {severe_count} challenging topic(s). "
                "Break them into smaller parts and practice with examples."
            )

        if moderate_count > 0:
            tips.append(
                f"Review {moderate_count} topic(s) that need reinforcement. "
                "Try explaining them in your own words."
            )

        # Check for confusion patterns
        high_confusion = [wp for wp in weak_points if wp.confusion_indicators >= 3]
        if high_confusion:
            tips.append(
                f"Concepts like '{high_confusion[0].topic}' may benefit from "
                "visual aids, diagrams, or alternative explanations."
            )

        # General tips
        if len(weak_points) > 3:
            tips.append("Don't try to tackle everything at once. Prioritize the hardest topics first.")
        else:
            tips.append("Use spaced repetition: review these topics over multiple short sessions.")

        tips.append("Consider working through practice problems to solidify understanding.")

        return tips

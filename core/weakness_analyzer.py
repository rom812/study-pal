"""Weakness tracking and session analysis for identifying learning struggles."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


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


class WeaknessAnalyzer:
    """
    Analyzes tutoring session conversations to identify topics where the user struggles.

    This analyzer looks for patterns that indicate difficulty:
    - Repeated questions on the same topic
    - Confusion indicators in user messages
    - Requests for clarification or simpler explanations
    - Multiple attempts to understand the same concept
    """

    # Keywords that indicate confusion or struggle
    CONFUSION_KEYWORDS = [
        "don't understand",
        "don't get",
        "confused",
        "confusing",
        "lost",
        "stuck",
        "unclear",
        "not clear",
        "what do you mean",
        "can you explain",
        "explain again",
        "still don't",
        "still confused",
        "make sense",
        "doesn't make sense",
        "not making sense",
        "i'm lost",
        "help me understand",
        "struggling",
        "difficult",
        "hard to",
        "complicated",
    ]

    # Phrases requesting simpler explanations
    SIMPLIFICATION_REQUESTS = [
        "simpler",
        "easier way",
        "basic terms",
        "layman",
        "eli5",
        "explain like",
        "dumb it down",
        "break it down",
        "step by step",
    ]

    def __init__(
        self,
        min_frequency: int = 2,
        min_confusion_signals: int = 1,
    ):
        """
        Initialize the weakness analyzer.

        Args:
            min_frequency: Minimum times a topic must appear to be considered a weak point
            min_confusion_signals: Minimum confusion indicators to flag as weak point
        """
        self.min_frequency = min_frequency
        self.min_confusion_signals = min_confusion_signals

    def analyze_conversation(
        self, messages: list[BaseMessage], session_topic: str | None = None
    ) -> SessionRecommendations:
        """
        Analyze a conversation to identify weak points and generate recommendations.

        Args:
            messages: List of conversation messages (HumanMessage and AIMessage)
            session_topic: Optional general topic of the session

        Returns:
            SessionRecommendations with identified weak points and suggestions
        """
        # Extract topics and detect struggles
        topic_mentions = self._extract_topics(messages)
        confusion_signals = self._detect_confusion_signals(messages)
        repeated_topics = self._find_repeated_topics(messages)

        # Build weak points
        weak_points = self._build_weak_points(
            topic_mentions, confusion_signals, repeated_topics, messages
        )

        # Sort by severity
        weak_points.sort(
            key=lambda wp: (
                wp.difficulty_level == "severe",
                wp.difficulty_level == "moderate",
                wp.frequency,
            ),
            reverse=True,
        )

        # Generate recommendations
        priority_topics = [wp.topic for wp in weak_points[:5]]  # Top 5
        suggested_focus_time = self._calculate_focus_time(weak_points)
        study_tips = self._generate_study_tips(weak_points)
        summary = self._generate_session_summary(messages, weak_points, session_topic)

        return SessionRecommendations(
            weak_points=weak_points,
            priority_topics=priority_topics,
            suggested_focus_time=suggested_focus_time,
            study_approach_tips=study_tips,
            session_summary=summary,
        )

    def _extract_topics(self, messages: list[BaseMessage]) -> Counter:
        """
        Extract topics mentioned in the conversation.

        Uses simple keyword extraction. In a production system, this could use NLP/LLM.
        """
        topics = Counter()

        for msg in messages:
            if isinstance(msg, HumanMessage):
                text = msg.content.lower()
                # Look for common academic terms (simplified approach)
                # In production, use NER or LLM-based topic extraction
                words = re.findall(r'\b[a-z]{4,}\b', text)
                topics.update(words)

        return topics

    def _detect_confusion_signals(self, messages: list[BaseMessage]) -> dict[int, list[str]]:
        """
        Detect confusion signals in user messages.

        Returns:
            Dictionary mapping message index to list of detected confusion phrases
        """
        confusion_map = {}

        for idx, msg in enumerate(messages):
            if isinstance(msg, HumanMessage):
                text = msg.content.lower()
                detected = []

                # Check for confusion keywords
                for keyword in self.CONFUSION_KEYWORDS:
                    if keyword in text:
                        detected.append(keyword)

                # Check for simplification requests
                for phrase in self.SIMPLIFICATION_REQUESTS:
                    if phrase in text:
                        detected.append(f"requested: {phrase}")

                if detected:
                    confusion_map[idx] = detected

        return confusion_map

    def _find_repeated_topics(self, messages: list[BaseMessage]) -> dict[str, int]:
        """
        Find topics that are asked about multiple times.

        Returns:
            Dictionary mapping topic to number of times it was mentioned
        """
        # Track consecutive similar questions (simplified approach)
        topic_counts = defaultdict(int)

        prev_words = set()
        for msg in messages:
            if isinstance(msg, HumanMessage):
                words = set(re.findall(r'\b[a-z]{4,}\b', msg.content.lower()))

                # Check overlap with previous question
                overlap = words & prev_words
                if overlap and len(overlap) >= 2:
                    # Similar topic asked again
                    topic_key = " ".join(sorted(overlap)[:3])
                    topic_counts[topic_key] += 1

                prev_words = words

        return topic_counts

    def _build_weak_points(
        self,
        topic_mentions: Counter,
        confusion_signals: dict[int, list[str]],
        repeated_topics: dict[str, int],
        messages: list[BaseMessage],
    ) -> list[WeakPoint]:
        """Build WeakPoint objects from analysis results."""
        weak_points_dict: dict[str, WeakPoint] = {}

        # Build exclusion set: words that are confusion indicators, not topics
        exclusion_words = set()
        for keyword in self.CONFUSION_KEYWORDS:
            exclusion_words.update(keyword.lower().split())
        for phrase in self.SIMPLIFICATION_REQUESTS:
            exclusion_words.update(phrase.lower().split())

        # Process confusion signals
        for msg_idx, signals in confusion_signals.items():
            if msg_idx < len(messages):
                msg = messages[msg_idx]
                text = msg.content

                # Extract likely topic from the confused message
                words = re.findall(r'\b[a-z]{3,}\b', text.lower())
                if words:
                    # Filter out confusion signal words and find meaningful topic
                    topic_candidates = [
                        w for w in words
                        if len(w) >= 3 and w not in exclusion_words
                    ]

                    if topic_candidates:
                        # Use the most frequently mentioned word as the topic
                        # (more likely to be the actual subject than a random word)
                        topic = max(topic_candidates, key=lambda w: topic_mentions.get(w, 0))

                        if topic not in weak_points_dict:
                            weak_points_dict[topic] = WeakPoint(
                                topic=topic,
                                difficulty_level="mild",
                                evidence=[text[:100]],
                                frequency=1,
                                confusion_indicators=len(signals),
                            )
                        else:
                            weak_points_dict[topic].evidence.append(text[:100])
                            weak_points_dict[topic].confusion_indicators += len(signals)
                            weak_points_dict[topic].frequency += 1

        # Process repeated topics
        for topic, count in repeated_topics.items():
            if count >= self.min_frequency:
                if topic not in weak_points_dict:
                    weak_points_dict[topic] = WeakPoint(
                        topic=topic,
                        difficulty_level="mild",
                        evidence=[f"Asked {count} times"],
                        frequency=count,
                    )
                else:
                    weak_points_dict[topic].frequency += count

        # Recalculate difficulty levels
        for wp in weak_points_dict.values():
            wp.__post_init__()

        # Filter weak points that meet minimum criteria
        return [
            wp
            for wp in weak_points_dict.values()
            if wp.frequency >= self.min_frequency
            or wp.confusion_indicators >= self.min_confusion_signals
        ]

    def _calculate_focus_time(self, weak_points: list[WeakPoint]) -> dict[str, int]:
        """
        Calculate suggested study time for each weak point.

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

    def _generate_study_tips(self, weak_points: list[WeakPoint]) -> list[str]:
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

    def _generate_session_summary(
        self,
        messages: list[BaseMessage],
        weak_points: list[WeakPoint],
        session_topic: str | None,
    ) -> str:
        """Generate a human-readable session summary."""
        total_messages = len([m for m in messages if isinstance(m, HumanMessage)])

        summary_parts = []

        if session_topic:
            summary_parts.append(f"Session focus: {session_topic}")

        summary_parts.append(f"Total questions asked: {total_messages}")

        if weak_points:
            summary_parts.append(
                f"Identified {len(weak_points)} area(s) for improvement: "
                f"{', '.join(wp.topic for wp in weak_points[:3])}"
            )

            severe = [wp for wp in weak_points if wp.difficulty_level == "severe"]
            if severe:
                summary_parts.append(
                    f"Priority topic(s) requiring extra attention: "
                    f"{', '.join(wp.topic for wp in severe[:2])}"
                )
        else:
            summary_parts.append("No significant difficulties detected. Strong session!")

        return " | ".join(summary_parts)


def create_weakness_analyzer(
    min_frequency: int = 2, min_confusion_signals: int = 1
) -> WeaknessAnalyzer:
    """
    Factory function to create a WeaknessAnalyzer with custom settings.

    Args:
        min_frequency: Minimum times a topic must appear to be considered weak
        min_confusion_signals: Minimum confusion indicators to flag as weak point

    Returns:
        Configured WeaknessAnalyzer instance
    """
    return WeaknessAnalyzer(
        min_frequency=min_frequency, min_confusion_signals=min_confusion_signals
    )
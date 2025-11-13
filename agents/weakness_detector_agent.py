"""Weakness detector agent for analyzing student struggles in conversations."""

from __future__ import annotations

import json
import os
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage

from core.weakness_analyzer import SessionRecommendations, WeakPoint

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class WeaknessDetectorAgent:
    """
    Uses LLM to analyze conversation and identify topics where student struggles.

    This provides deeper, context-aware analysis compared to rule-based approaches.
    Identifies:
    - Actual topics (not confusion signal words)
    - Nuanced struggle patterns
    - Conceptual confusion
    - Severity levels based on conversation context
    """

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize LLM weakness detector.

        Args:
            model: OpenAI model to use (default: gpt-4o-mini for cost-effectiveness)
            temperature: Low temperature for consistent analysis
        """
        if OpenAI is None:
            raise ImportError(
                "The 'openai' package is required. Install it via `pip install openai`."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def analyze_conversation(
        self, messages: list[BaseMessage], session_topic: str | None = None
    ) -> SessionRecommendations:
        """
        Analyze conversation to identify weak points and generate recommendations using LLM.

        Args:
            messages: List of conversation messages
            session_topic: Optional general topic of the session

        Returns:
            SessionRecommendations object with:
            - weak_points: List of WeakPoint objects
            - priority_topics: Topics ordered by severity
            - suggested_focus_time: Dict of topic -> minutes
            - study_approach_tips: List of personalized tips
            - session_summary: Overall session assessment
        """
        # Build conversation transcript
        transcript = self._build_transcript(messages)

        # Create analysis prompt
        prompt = self._build_analysis_prompt(transcript, session_topic)

        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            # Parse response
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from LLM")

            result = json.loads(result_text)

            # Convert to SessionRecommendations object
            return self._convert_to_recommendations(result)

        except Exception as e:
            print(f"[llm_detector] Error during LLM analysis: {e}")
            # Return empty recommendations on error
            return SessionRecommendations(
                weak_points=[],
                priority_topics=[],
                suggested_focus_time={},
                study_approach_tips=["Analysis failed. Please try again."],
                session_summary="Analysis failed"
            )

    def _convert_to_recommendations(self, result: dict) -> SessionRecommendations:
        """
        Convert LLM JSON result to SessionRecommendations object.

        Args:
            result: Dict with LLM analysis results

        Returns:
            SessionRecommendations object
        """
        # Convert weak_points dicts to WeakPoint objects
        weak_points = []
        for wp_data in result.get("weak_points", []):
            weak_point = WeakPoint(
                topic=wp_data.get("topic", "unknown"),
                difficulty_level=wp_data.get("difficulty_level", "mild"),
                evidence=wp_data.get("evidence", []),
                frequency=wp_data.get("frequency", 1),
                confusion_indicators=wp_data.get("confusion_indicators", 0),
            )
            weak_points.append(weak_point)

        # Build SessionRecommendations
        return SessionRecommendations(
            weak_points=weak_points,
            priority_topics=result.get("priority_topics", []),
            suggested_focus_time=result.get("suggested_focus_time", {}),
            study_approach_tips=result.get("study_approach_tips", []),
            session_summary=result.get("session_summary", "No summary available"),
        )

    def _build_transcript(self, messages: list[BaseMessage]) -> str:
        """Build a readable transcript from messages."""
        transcript_lines = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                transcript_lines.append(f"Student: {msg.content}")
            else:
                # AI message
                transcript_lines.append(f"Tutor: {msg.content}")

        return "\n".join(transcript_lines)

    def _build_analysis_prompt(self, transcript: str, session_topic: str | None) -> str:
        """Build the analysis prompt for LLM."""
        prompt_parts = []

        if session_topic:
            prompt_parts.append(f"Session Topic: {session_topic}\n")

        prompt_parts.append("Conversation Transcript:")
        prompt_parts.append(transcript)
        prompt_parts.append("\nAnalyze this tutoring session and identify topics where the student struggled.")

        return "\n".join(prompt_parts)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt with examples and instructions.

        This is the core of the detector - teaches the LLM how to identify struggles.
        """
        return """You are an expert educational psychologist analyzing student-tutor conversations to identify learning difficulties.

Your task: Identify topics where the student genuinely struggled, generate personalized study recommendations, and provide actionable advice.

# Key Indicators of Struggle:

1. **Confusion Signals**:
   - "I don't understand..."
   - "I'm confused about..."
   - "This doesn't make sense..."
   - "I'm lost..."

2. **Repeated Clarifications**:
   - Asking about the same concept multiple times
   - Requesting "explain again" or "simpler explanation"
   - Rephrasing the same question differently

3. **Conceptual Confusion**:
   - Mixing up related concepts
   - Incorrect analogies or comparisons
   - Misunderstanding cause-and-effect

4. **Implicit Struggles**:
   - Long response times (indicated by short, uncertain messages)
   - Incomplete thoughts or sentence fragments
   - Defensive language ("I think I get it but...")

# What NOT to Mark as Weak Points:
- Simple clarification questions (one-time, specific)
- General curiosity questions
- Asking for examples (if not confused)
- Signal words like "again", "simpler" (extract the TOPIC instead)

# Examples:

## Example 1: Clear Struggle
Student: "What is a derivative?"
Tutor: [explains]
Student: "I'm still confused about derivatives"
Tutor: [explains]
Student: "Can you explain derivatives simpler?"

Analysis:
- Topic: "derivatives"
- Difficulty: "moderate"
- Evidence: Asked 3 times, explicit confusion, requested simpler explanation
- Reasoning: "Student asked about derivatives multiple times with explicit confusion signals"

## Example 2: Not a Weak Point
Student: "What is integration?"
Tutor: [explains]
Student: "Cool, can you give an example?"
Tutor: [example]
Student: "Got it, thanks!"

Analysis: No weak points (normal learning flow)

## Example 3: Severe Struggle
Student: "What's the difference between acceleration and velocity?"
Tutor: [explains]
Student: "So acceleration is just speed?"
Tutor: "No, velocity includes direction..."
Student: "I don't get it, isn't that the same as acceleration?"
Tutor: [explains again]
Student: "I'm so lost on this"

Analysis:
- Topic: "acceleration and velocity"
- Difficulty: "severe"
- Evidence: Conceptual confusion, mixing concepts, multiple failed attempts, explicit frustration
- Reasoning: "Student shows fundamental confusion between related concepts despite multiple explanations"

# Output Format (JSON):

{
  "weak_points": [
    {
      "topic": "specific topic name (not 'again' or 'simpler')",
      "difficulty_level": "mild" | "moderate" | "severe",
      "evidence": ["direct quote 1", "direct quote 2"],
      "frequency": <number of times topic appeared>,
      "confusion_indicators": <number of confusion signals detected>
    }
  ],
  "priority_topics": ["topic1", "topic2", ...],  // Ordered by severity (severe first)
  "suggested_focus_time": {
    "topic1": <minutes>,
    "topic2": <minutes>
  },
  "study_approach_tips": [
    "Actionable tip 1",
    "Actionable tip 2",
    ...
  ],
  "session_summary": "1-2 sentence summary of overall session performance"
}

# Difficulty Levels:
- **mild**: Asked 1-2 times, minor confusion
- **moderate**: Asked 3+ times, explicit confusion, requested simpler explanations
- **severe**: 5+ mentions, conceptual confusion, mixing concepts, high frustration

# Focus Time Calculation (suggested study minutes):
- **severe**: 30-50 minutes base (add 5 min per extra occurrence, max +20)
- **moderate**: 20-30 minutes base (add 3-5 min per extra occurrence, max +15)
- **mild**: 10-15 minutes base (add 2-3 min per extra occurrence, max +10)

# Study Approach Tips Guidelines:
Generate 3-5 contextual tips based on patterns you observe:
- If severe topics exist: "Focus on [count] challenging topic(s). Break them into smaller parts and practice with examples."
- If moderate topics exist: "Review [count] topic(s) that need reinforcement. Try explaining them in your own words."
- If high confusion (3+ signals): "Concepts like '[topic]' may benefit from visual aids, diagrams, or alternative explanations."
- If many topics (>3): "Don't try to tackle everything at once. Prioritize the hardest topics first."
- If few topics (≤3): "Use spaced repetition: review these topics over multiple short sessions."
- Always include: "Consider working through practice problems to solidify understanding."
- If no weak points: "Great session! Continue building on what you learned."

Make tips specific to the actual topics and struggles observed in the conversation.

Now analyze the conversation and respond with JSON only."""


def create_weakness_detector_agent(
    model: str = "gpt-4o-mini", temperature: float = 0.1
) -> WeaknessDetectorAgent:
    """
    Factory function to create a weakness detector agent.

    Args:
        model: OpenAI model to use
        temperature: Temperature for LLM (low = more consistent)

    Returns:
        Configured WeaknessDetectorAgent instance
    """
    return WeaknessDetectorAgent(model=model, temperature=temperature)

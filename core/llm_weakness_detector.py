"""LLM-based weakness detection for nuanced analysis of student struggles."""

from __future__ import annotations

import json
import os
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMWeaknessDetector:
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
    ) -> dict:
        """
        Analyze conversation to identify weak points using LLM.

        Args:
            messages: List of conversation messages
            session_topic: Optional general topic of the session

        Returns:
            Dictionary with detected weak points:
            {
                "weak_points": [
                    {
                        "topic": str,
                        "difficulty_level": "mild" | "moderate" | "severe",
                        "evidence": [str],
                        "reasoning": str
                    }
                ],
                "session_summary": str
            }
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
            return result

        except Exception as e:
            print(f"[llm_detector] Error during LLM analysis: {e}")
            return {"weak_points": [], "session_summary": "Analysis failed"}

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

Your task: Identify topics where the student genuinely struggled, not just asked questions.

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
      "reasoning": "brief explanation of why this is a weak point"
    }
  ],
  "session_summary": "1-2 sentence summary of overall session performance"
}

# Difficulty Levels:
- **mild**: Asked 1-2 times, minor confusion
- **moderate**: Asked 3+ times, explicit confusion, requested simpler explanations
- **severe**: 5+ mentions, conceptual confusion, mixing concepts, high frustration

Now analyze the conversation and respond with JSON only."""


def create_llm_weakness_detector(
    model: str = "gpt-4o-mini", temperature: float = 0.1
) -> LLMWeaknessDetector:
    """
    Factory function to create an LLM weakness detector.

    Args:
        model: OpenAI model to use
        temperature: Temperature for LLM (low = more consistent)

    Returns:
        Configured LLMWeaknessDetector instance
    """
    return LLMWeaknessDetector(model=model, temperature=temperature)

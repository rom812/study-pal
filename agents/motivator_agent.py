"""Motivator agent crafts persona-aligned encouragement."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

try:  # pragma: no cover - optional dependency during tests
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from pydantic import BaseModel, Field

from .quote_store import Quote
from .user_profile import UserProfile, UserProfileStore

try:
    from .quote_scraper import WebSearchQuoteScraper
except ImportError:
    WebSearchQuoteScraper = None  # type: ignore[assignment, misc]


class MotivationLLM(Protocol):
    """LLM used to compose personalized motivational messages."""

    def generate(
        self,
        *,
        persona: str,
        quote: Quote,
        profile: UserProfile,
    ) -> str: ...


class MotivationMessage(BaseModel):
    """Validated message delivered to the user."""

    text: str
    source: str
    persona_style: str
    user_name: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class MotivatorAgent:
    """Produces personalized motivational messages using web-scraped quotes."""

    profile_store: UserProfileStore | None = None
    llm: MotivationLLM | None = None

    def craft_personalized_message(
        self,
        user_id: str,
        scraper: WebSearchQuoteScraper | None = None,
    ) -> MotivationMessage:
        """
        Create a personalized motivational message for the user.

        This is the main entry point for generating motivation:
        1. Loads user profile (with weaknesses, persona, name, goals)
        2. Scrapes a quote from the web for the user's primary persona
        3. Uses LLM to craft a personalized message addressing their weaknesses

        Example flow:
            Profile: name="Rom", persona="DJ Khaled", weaknesses=["procrastination"], goal="finding a job"
            Output: "Don't play yourself" — DJ Khaled
                    Rom, I know you're struggling with procrastination, but don't ever play yourself!
                    You only have one life and you must grasp it and find that job.

        Args:
            user_id: User identifier
            scraper: Optional quote scraper (creates default if None)

        Returns:
            MotivationMessage with personalized content
        """
        # Load user profile
        profile = self._load_profile(user_id) if self.profile_store else None

        if not profile:
            raise ValueError(f"No profile found for user_id: {user_id}")

        persona = profile.primary_persona or "default"

        # Create scraper if not provided
        if scraper is None:
            if WebSearchQuoteScraper is None:
                raise ImportError(
                    "WebSearchQuoteScraper is not available. Ensure quote_scraper.py is imported correctly."
                )
            scraper = WebSearchQuoteScraper()

        # Scrape quotes for the persona
        print(f"[motivator] Scraping quotes for {persona}...")
        quotes = scraper.scrape_quotes(persona, limit=3)

        if not quotes:
            raise RuntimeError(f"No quotes found for persona: {persona}")

        # Select first quote
        quote = quotes[0]
        print(f"[motivator] Selected quote: {quote.text[:50]}...")

        # Generate personalized message using LLM
        if not self.llm:
            raise RuntimeError("LLM is required for personalized message generation")

        print("[motivator] Generating personalized message...")
        text = self.llm.generate(
            persona=persona,
            quote=quote,
            profile=profile,
        )

        # Create the message
        message = MotivationMessage(
            text=text,
            source=str(quote.source_url) if quote.source_url else "web_search",
            persona_style=persona,
            user_name=profile.name,
        )

        # Update profile
        if self.profile_store:
            profile.last_motivation_at = message.timestamp
            self.profile_store.save(profile)

        return message

    def _load_profile(self, user_id: str) -> UserProfile:
        """Load or create user profile."""
        assert self.profile_store is not None
        try:
            return self.profile_store.load(user_id)
        except FileNotFoundError:
            profile = UserProfile(user_id=user_id, name=user_id)
            self.profile_store.save(profile)
            return profile


class OpenAIMotivationModel:
    """LLM wrapper that composes motivational messages via OpenAI."""

    SYSTEM_PROMPT = (
        "You are Study Pal's Motivator Agent. "
        "You speak on behalf of the chosen persona to encourage a student. "
        "Always follow this structure:\n"
        '1) First line: an exact quote from the persona (if provided), formatted as "quote" — Persona Name. '
        "   If no quote is provided, craft a short, persona-aligned mantra.\n"
        "2) Second line: a personalized message directly addressing the student by name. "
        "   Reference their weaknesses/struggles, study goals, or current focus. "
        "   Acknowledge their challenges and provide authentic encouragement in the persona's voice. "
        "   Be uplifting but concise (2-3 sentences max).\n\n"
        "Example:\n"
        "Input: persona=DJ Khaled, name=Rom, weaknesses=[procrastination], main_goal=finding a job\n"
        'Output: "Don\'t play yourself" — DJ Khaled\n'
        "Rom, I know you're struggling with procrastination, but don't ever play yourself! "
        "You only have one life and you must grasp it and find that job. The key to success is taking action today.\n\n"
        "Never add extra commentary. Avoid emojis. Stay authentic to the persona's tone and speaking style."
    )

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.5,
    ) -> None:
        if OpenAI is None:  # pragma: no cover - external dependency guard
            raise ImportError(
                "The 'openai' package is required for OpenAIMotivationModel. Install it via `pip install openai`."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def generate(
        self,
        *,
        persona: str,
        quote: Quote,
        profile: UserProfile,
    ) -> str:
        """Generate personalized motivational message using the quote and user profile."""
        payload = {
            "persona": persona,
            "quote": quote.model_dump(mode="json", exclude_none=True),
            "user_profile": profile.model_dump(mode="json", exclude_none=True),
        }

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Compose the motivation for the following context:\n"
                    f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
                ),
            },
        ]

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )

        message = response.choices[0].message.content
        if not message:
            raise RuntimeError("OpenAI returned an empty message.")
        return message

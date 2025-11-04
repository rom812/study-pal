"""Motivator agent crafts persona-aligned encouragement."""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

try:  # pragma: no cover - optional dependency during tests
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from pydantic import BaseModel, Field

from .quote_store import Quote, QuoteStore
from .user_profile import UserProfile, UserProfileStore

try:
    from .quote_scraper import WebSearchQuoteScraper, PersonalizedQuoteGenerator
except ImportError:
    WebSearchQuoteScraper = None  # type: ignore[assignment, misc]
    PersonalizedQuoteGenerator = None  # type: ignore[assignment, misc]


class InspirationFetcher(Protocol):
    """External data source for quotes or stories."""

    def fetch(self, persona: str) -> dict:
        ...


class MotivationLLM(Protocol):
    """LLM used to compose personalized motivational messages."""

    def generate(
        self,
        *,
        persona: str,
        quote: Quote | None,
        profile: UserProfile | None,
        tag: str | None,
    ) -> str:
        ...


class MotivationMessage(BaseModel):
    """Validated message delivered to the user."""

    text: str
    source: str
    persona_style: str
    user_name: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class MotivatorAgent:
    """Produces motivational messaging cycles."""

    fetcher: InspirationFetcher | None = None
    profile_store: UserProfileStore | None = None
    quote_store: QuoteStore | None = None
    llm: MotivationLLM | None = None

    def craft_message(
        self,
        user_id: str,
        persona: str | None = None,
        tag: str | None = None,
    ) -> MotivationMessage:
        """Return a persona-specific motivational message."""
        profile = self._load_profile(user_id) if self.profile_store else None
        persona_to_use = persona or (profile.primary_persona if profile else "default")

        quote = self._select_quote(persona_to_use, profile, tag)

        text, source = self._compose_message(persona_to_use, profile, quote, tag, user_id)

        message = MotivationMessage(
            text=text,
            source=source,
            persona_style=persona_to_use,
            user_name=profile.name if profile else None,
        )

        if profile and self.profile_store:
            profile.last_motivation_at = message.timestamp
            self.profile_store.save(profile)

        return message

    def craft_message_from_web(
        self,
        user_id: str,
        persona: str,
        scraper: WebSearchQuoteScraper | None = None,
        personalizer: PersonalizedQuoteGenerator | None = None,
        save_to_store: bool = True,
    ) -> MotivationMessage:
        """
        Scrape quotes from the web for a persona and create a deeply personalized message.

        Args:
            user_id: The user to create the message for
            persona: The persona to scrape quotes from (e.g., "Isaac Newton", "Marie Curie")
            scraper: Optional quote scraper (creates default if None)
            personalizer: Optional personalizer (creates default if None)
            save_to_store: If True, saves the scraped quote to the quote store

        Returns:
            MotivationMessage with personalized content
        """
        # Load user profile
        profile = self._load_profile(user_id) if self.profile_store else None

        # Create scraper if not provided
        if scraper is None:
            if WebSearchQuoteScraper is None:
                raise ImportError(
                    "WebSearchQuoteScraper is not available. "
                    "Ensure quote_scraper.py is imported correctly."
                )
            scraper = WebSearchQuoteScraper()

        # Scrape quotes for the persona
        print(f"[motivator] Scraping quotes for {persona}...")
        quotes = scraper.scrape_quotes(persona, limit=3)

        if not quotes:
            raise RuntimeError(f"No quotes found for persona: {persona}")

        # Select the best quote (first one for now, could be randomized)
        quote = quotes[0]

        # Save to quote store if requested
        if save_to_store and self.quote_store:
            self.quote_store.add([quote])
            print(f"[motivator] Added quote to store: {quote.text[:50]}...")

        # Create personalized message
        if personalizer is None:
            if PersonalizedQuoteGenerator is None:
                raise ImportError(
                    "PersonalizedQuoteGenerator is not available. "
                    "Ensure quote_scraper.py is imported correctly."
                )
            personalizer = PersonalizedQuoteGenerator()

        # Build user profile dict for personalization
        user_profile_dict = {
            "name": profile.name if profile else user_id,
            "user_id": user_id,
        }

        if profile:
            user_profile_dict.update({
                "current_focus": profile.current_focus,
                "study_topics": profile.study_topics,
                "traits": profile.traits,
                "goals": profile.goals,
                "primary_persona": profile.primary_persona,
            })

        print(f"[motivator] Generating personalized message...")
        text = personalizer.generate_personalized_message(quote, user_profile_dict)

        # Create the message
        message = MotivationMessage(
            text=text,
            source=str(quote.source_url) if quote.source_url else "web_search",
            persona_style=persona,
            user_name=profile.name if profile else None,
        )

        # Update profile
        if profile and self.profile_store:
            profile.last_motivation_at = message.timestamp
            self.profile_store.save(profile)

        return message

    # ------------------------------------------------------------------
    # Message generation helpers
    # ------------------------------------------------------------------
    def _compose_message(
        self,
        persona: str,
        profile: UserProfile | None,
        quote: Quote | None,
        tag: str | None,
        user_id: str,
    ) -> tuple[str, str]:
        """Compose the message using the LLM when available."""
        if self.llm:
            try:
                text = self.llm.generate(
                    persona=persona,
                    quote=quote,
                    profile=profile,
                    tag=tag,
                )
                if text.strip():
                    source = (
                        str(quote.source_url)
                        if quote and quote.source_url
                        else ("quote_store" if quote else "openai")
                    )
                    return text.strip(), source
            except Exception as exc:  # pragma: no cover - LLM errors fallback
                print(f"[motivator] LLM generation failed: {exc}")

        # Fallback path
        if quote:
            recipient = profile.name if profile else user_id
            focus = self._determine_focus(profile)
            quote_line = f"“{quote.text}” — {quote.persona}"
            personal_line = f"{recipient}, keep pushing toward {focus}."
            text = f"{quote_line}\n{personal_line}"
            source = str(quote.source_url) if quote.source_url else "quote_store"
        else:
            data = self.fetcher.fetch(persona) if self.fetcher else {}
            text = data.get("text", "Stay focused – greatness is built daily.")
            source = data.get("source", "fallback")

        return text, source

    def _select_quote(
        self,
        persona: str,
        profile: UserProfile | None,
        tag: str | None,
    ) -> Quote | None:
        if not self.quote_store:
            return None

        candidate_quotes: list[Quote] = []
        if tag:
            candidate_quotes.extend(self.quote_store.search_by_tag(tag, persona=persona))
        else:
            candidate_quotes.extend(self.quote_store.get_by_persona(persona))

        if profile and not candidate_quotes:
            desired_tags = self._derive_tags(profile)
            for desired_tag in desired_tags:
                candidate_quotes.extend(self.quote_store.search_by_tag(desired_tag, persona=persona))

        if not candidate_quotes:
            return None

        if profile:
            index = hash(profile.user_id + persona) % len(candidate_quotes)
            return candidate_quotes[index]

        return random.choice(candidate_quotes)

    @staticmethod
    def _derive_tags(profile: UserProfile) -> list[str]:
        trait_to_tag = {
            "procrastination": "focus",
            "burnout": "rest",
            "perfectionism": "self-belief",
            "fatigue": "rest",
            "doubt": "self-belief",
            "overwhelmed": "perseverance",
        }

        tags: list[str] = []
        for trait in profile.traits:
            mapped = trait_to_tag.get(trait.lower())
            if mapped and mapped not in tags:
                tags.append(mapped)
        return tags

    @staticmethod
    def _determine_focus(profile: UserProfile | None) -> str:
        if profile:
            if profile.current_focus:
                return profile.current_focus
            if profile.study_topics:
                return profile.study_topics[0]
        return "your goals"

    def _load_profile(self, user_id: str) -> UserProfile:
        assert self.profile_store is not None  # For type checking
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
        "1) First line: an exact quote from the persona (if provided), formatted as “quote” — Persona Name. "
        "   If no quote is provided, craft a short, persona-aligned mantra.\n"
        "2) Second line: a personalised message directly addressing the student by name. "
        "   Reference their study goals, current focus, or traits. Be uplifting but concise (max 2 sentences).\n"
        "Never add additional commentary. Avoid emojis. Stay authentic to the persona's tone."
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
        quote: Quote | None,
        profile: UserProfile | None,
        tag: str | None,
    ) -> str:
        payload = {
            "persona": persona,
            "quote": quote.model_dump(mode="json", exclude_none=True) if quote else None,
            "user_profile": profile.model_dump(mode="json", exclude_none=True) if profile else None,
            "requested_tag": tag,
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

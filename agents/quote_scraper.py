"""Web scraper for fetching inspirational quotes from various sources."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Protocol

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment]

from .quote_store import Quote


class QuoteScraper(Protocol):
    """Protocol for quote scraping implementations."""

    def scrape_quotes(self, persona: str, limit: int = 5) -> list[Quote]:
        """Scrape quotes for a given persona."""
        ...


@dataclass
class WebSearchQuoteScraper:
    """
    Uses web search and LLM to find and extract inspirational quotes.

    This implementation uses an LLM to search for and extract quotes,
    avoiding complex web scraping dependencies.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ) -> None:
        if OpenAI is None:
            raise ImportError(
                "The 'openai' package is required for WebSearchQuoteScraper. Install it via `pip install openai`."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def scrape_quotes(self, persona: str, limit: int = 5) -> list[Quote]:
        """
        Use LLM to generate a list of well-known inspirational quotes from the persona.

        Args:
            persona: Name of the person to fetch quotes from
            limit: Maximum number of quotes to return

        Returns:
            List of Quote objects
        """
        system_prompt = (
            "You are a quote researcher. Your task is to provide accurate, "
            "well-known inspirational quotes from famous figures (without changing them). "
            "Return ONLY valid JSON in the exact format specified, with no additional text."
        )

        user_prompt = f"""Find {limit} inspirational and motivational quotes from {persona}.

Focus on quotes about:
- Perseverance and determination
- Learning and education
- Overcoming challenges
- Focus and discipline
- Self-belief

Return ONLY a JSON array with this exact structure:
[
  {{
    "text": "The exact quote text",
    "persona": "{persona}",
    "tags": ["tag1", "tag2"],
    "source_url": "A real source URL if known, or null"
  }}
]

IMPORTANT:
- Return ONLY the JSON array, no other text
- Quotes must be real and attributable to {persona}
- Tags should be from: focus, perseverance, self-belief, rest, discipline, learning
- Each quote should have 1-3 tags"""

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("OpenAI returned empty content")

            # Clean up the response - remove markdown code blocks if present
            content = content.strip()
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            # Parse JSON
            quotes_data = json.loads(content)

            # Convert to Quote objects
            quotes = []
            for q_data in quotes_data:
                quote = Quote(
                    text=q_data["text"],
                    persona=q_data["persona"],
                    tags=q_data.get("tags", []),
                    source_url=q_data.get("source_url"),
                )
                quotes.append(quote)

            return quotes[:limit]

        except json.JSONDecodeError as e:
            print(f"[quote_scraper] Failed to parse JSON response: {e}")
            print(f"[quote_scraper] Raw content: {content}")
            return []
        except Exception as e:
            print(f"[quote_scraper] Error scraping quotes: {e}")
            return []


class PersonalizedQuoteGenerator:
    """
    Generates personalized motivational messages by combining scraped quotes
    with deep personalization based on user profile.
    """

    SYSTEM_PROMPT = (
        "You are Study Pal's Advanced Motivator Agent. "
        "You create deeply personalized motivational messages by connecting "
        "a persona's quote to the user's specific situation, struggles, and goals.\n\n"
        "Structure your response as follows:\n"
        '1) First line: The exact quote, formatted as "quote" - Persona Name\n'
        "2) Following lines: A thoughtful, personalized reflection (2-4 sentences) that:\n"
        "   - Explains why this quote resonates with the user's specific situation\n"
        "   - References the persona's own struggles/journey that parallel the user's challenges\n"
        "   - Connects to the user's goals, current focus, or traits\n"
        "   - Provides genuine encouragement\n\n"
        "Be authentic, warm, and specific. Use the user's name naturally. "
        "Avoid generic advice. No emojis."
    )

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
    ) -> None:
        if OpenAI is None:
            raise ImportError(
                "The 'openai' package is required for PersonalizedQuoteGenerator. Install it via `pip install openai`."
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

        self._client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def generate_personalized_message(
        self,
        quote: Quote,
        user_profile: dict,
    ) -> str:
        """
        Generate a deeply personalized motivational message.

        Args:
            quote: The Quote object to personalize
            user_profile: Dictionary containing user information (name, traits, goals, etc.)

        Returns:
            Personalized motivational message string
        """
        context = {
            "quote": {
                "text": quote.text,
                "persona": quote.persona,
                "tags": quote.tags,
            },
            "user": user_profile,
        }

        user_prompt = (
            "Create a personalized motivational message using the quote and user context below.\n\n"
            "Make it deeply personal - explain how the persona's own journey and struggles "
            "parallel what the user is going through. Be specific and genuine.\n\n"
            f"Context:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
            )

            message = response.choices[0].message.content
            if not message:
                raise RuntimeError("OpenAI returned empty message")

            return message.strip()

        except Exception as e:
            print(f"[personalized_generator] Error generating message: {e}")
            # Fallback to basic format
            return f'"{quote.text}" — {quote.persona}\n\nLet this wisdom guide you on your journey.'

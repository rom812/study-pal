"""Tests for MotivatorAgent simplified personalization."""

from __future__ import annotations
from pathlib import Path

from agents.motivator_agent import MotivatorAgent, Quote
from agents.user_profile import UserProfile, UserProfileStore


class DummyLLM:
    """Mock LLM for testing."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, *, persona: str, quote: Quote, profile: UserProfile) -> str:
        """Generate a mock personalized message."""
        self.calls.append({
            "persona": persona,
            "quote_text": quote.text,
            "profile_name": profile.name,
            "weaknesses": profile.traits,
        })

        # Simulate DJ Khaled example output
        weaknesses_str = ", ".join(profile.traits) if profile.traits else "challenges"
        return (
            f'"{quote.text}" — {persona}\n'
            f'{profile.name}, I know you\'re struggling with {weaknesses_str}, but stay focused! '
            f'Keep working toward {profile.goals[0] if profile.goals else "your goals"}.'
        )


class DummyScraper:
    """Mock web scraper for testing."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def scrape_quotes(self, persona: str, limit: int = 3) -> list[Quote]:
        """Return mock quotes."""
        self.calls.append(persona)
        return [
            Quote(
                text="Don't play yourself",
                persona=persona,
                tags=["motivation", "focus"],
                source_url="https://example.com/quote"
            ),
            Quote(
                text="Another one",
                persona=persona,
                tags=["persistence"],
            ),
        ]


def test_craft_personalized_message(tmp_path: Path) -> None:
    """Test the main simplified craft_personalized_message flow."""
    # Setup
    profile_store = UserProfileStore(tmp_path / "profiles")
    profile = UserProfile(
        user_id="rom",
        name="Rom",
        primary_persona="DJ Khaled",
        traits=["procrastination"],
        goals=["finding a job"],
    )
    profile_store.save(profile)

    llm = DummyLLM()
    scraper = DummyScraper()
    agent = MotivatorAgent(profile_store=profile_store, llm=llm)

    # Execute
    message = agent.craft_personalized_message(user_id="rom", scraper=scraper)

    # Verify scraper was called with correct persona
    assert scraper.calls == ["DJ Khaled"]

    # Verify LLM was called with correct data
    assert len(llm.calls) == 1
    assert llm.calls[0]["persona"] == "DJ Khaled"
    assert llm.calls[0]["quote_text"] == "Don't play yourself"
    assert llm.calls[0]["profile_name"] == "Rom"
    assert llm.calls[0]["weaknesses"] == ["procrastination"]

    # Verify message structure
    assert message.persona_style == "DJ Khaled"
    assert message.user_name == "Rom"
    assert "Don't play yourself" in message.text
    assert "Rom" in message.text
    assert "procrastination" in message.text
    assert "finding a job" in message.text
    assert message.source == "https://example.com/quote"

    # Verify profile was updated
    saved_profile = profile_store.load("rom")
    assert saved_profile.last_motivation_at is not None


def test_craft_personalized_message_requires_llm(tmp_path: Path) -> None:
    """Test that LLM is required for message generation."""
    profile_store = UserProfileStore(tmp_path / "profiles")
    profile = UserProfile(
        user_id="rom",
        name="Rom",
        primary_persona="DJ Khaled",
    )
    profile_store.save(profile)

    agent = MotivatorAgent(profile_store=profile_store, llm=None)
    scraper = DummyScraper()

    try:
        agent.craft_personalized_message(user_id="rom", scraper=scraper)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "LLM is required" in str(e)


def test_craft_personalized_message_auto_creates_profile(tmp_path: Path) -> None:
    """Test that profile is auto-created if it doesn't exist."""
    profile_store = UserProfileStore(tmp_path / "profiles")
    llm = DummyLLM()
    scraper = DummyScraper()
    agent = MotivatorAgent(profile_store=profile_store, llm=llm)

    # Create profile with default persona
    profile = UserProfile(
        user_id="new_user",
        name="new_user",
        primary_persona="Steve Jobs",
    )
    profile_store.save(profile)

    message = agent.craft_personalized_message(user_id="new_user", scraper=scraper)

    # Profile should be loaded and used
    assert message.user_name == "new_user"
    assert message.persona_style == "Steve Jobs"

"""Tests for MotivatorAgent personalization scaffolding."""

from __future__ import annotations
from pathlib import Path

from agents.motivator_agent import MotivatorAgent
from agents.quote_store import Quote, QuoteStore
from agents.user_profile import UserProfile, UserProfileStore


class DummyFetcher:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def fetch(self, persona: str) -> dict:
        self.calls.append(persona)
        return {"text": f"Quote from {persona}", "source": "dummy"}


class DummyLLM:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, *, persona, quote, profile, tag) -> str:
        self.calls.append(
            {
                "persona": persona,
                "quote": quote.text if quote else None,
                "profile": profile.name if profile else None,
                "tag": tag,
            }
        )
        student = profile.name if profile else "Friend"
        if quote:
            return f"“{quote.text}” — {persona}\n{student}, you got this!"
        return f"{persona} urges you to stay focused, {student}!"


def test_craft_message_uses_profile_persona(tmp_path: Path) -> None:
    store = UserProfileStore(tmp_path)
    profile = UserProfile(user_id="rom", name="Rom", primary_persona="Kobe Bryant")
    store.save(profile)

    fetcher = DummyFetcher()
    agent = MotivatorAgent(fetcher=fetcher, profile_store=store)

    message = agent.craft_message(user_id="rom")

    assert message.persona_style == "Kobe Bryant"
    assert message.user_name == "Rom"
    assert message.text.startswith("Quote from Kobe Bryant")
    assert fetcher.calls == ["Kobe Bryant"]

    saved = store.load("rom")
    assert saved.last_motivation_at is not None


def test_craft_message_allows_manual_persona(tmp_path: Path) -> None:
    fetcher = DummyFetcher()
    agent = MotivatorAgent(fetcher=fetcher, profile_store=None)

    message = agent.craft_message(user_id="any", persona="Marie Curie")
    print(message)
    assert message.persona_style == "Marie Curie"
    assert fetcher.calls == ["Marie Curie"]


def test_craft_message_prefers_cached_quotes_over_fetcher(tmp_path: Path) -> None:
    """Agent should use cached quotes from quote_store before falling back to fetcher."""
    quote_store = QuoteStore(tmp_path / "quotes.json")
    cached_quote = Quote(
        text="The only way to do great work is to love what you do.",
        persona="Steve Jobs",
        tags=["passion", "work"],
    )
    quote_store.add([cached_quote])

    fetcher = DummyFetcher()
    agent = MotivatorAgent(fetcher=fetcher, quote_store=quote_store)

    message = agent.craft_message(user_id="test_user", persona="Steve Jobs")

    # Should use cached quote, not fetcher
    assert message.text.startswith("“The only way to do great work is to love what you do.")
    assert message.source == "quote_store"
    assert message.persona_style == "Steve Jobs"
    assert fetcher.calls == []  # Fetcher should NOT be called


def test_craft_message_falls_back_to_fetcher_when_no_cache(tmp_path: Path) -> None:
    """Agent should fall back to fetcher when quote_store has no matching quotes."""
    quote_store = QuoteStore(tmp_path / "quotes.json")
    # Store has quotes for different persona
    quote_store.add(
        [Quote(text="Science quote", persona="Marie Curie", tags=["science"])]
    )

    fetcher = DummyFetcher()
    agent = MotivatorAgent(fetcher=fetcher, quote_store=quote_store)

    message = agent.craft_message(user_id="test_user", persona="Steve Jobs")
    print(message)
    # Should fall back to fetcher since no Steve Jobs quotes in cache
    assert message.text == "Quote from Steve Jobs"
    assert message.source == "dummy"
    assert message.persona_style == "Steve Jobs"
    assert fetcher.calls == ["Steve Jobs"]


def test_craft_message_supports_tag_filtering(tmp_path: Path) -> None:
    """Agent should support filtering quotes by tag."""
    quote_store = QuoteStore(tmp_path / "quotes.json")
    quotes = [
        Quote(text="Focus quote", persona="Steve Jobs", tags=["focus"]),
        Quote(text="Passion quote", persona="Steve Jobs", tags=["passion"]),
    ]
    quote_store.add(quotes)

    fetcher = DummyFetcher()
    agent = MotivatorAgent(fetcher=fetcher, quote_store=quote_store)

    message = agent.craft_message(user_id="test_user", persona="Steve Jobs", tag="focus")

    assert message.text.startswith("“Focus quote”")
    assert message.source == "quote_store"
    assert fetcher.calls == []  # Should not call fetcher


def test_craft_message_without_quote_store_uses_fetcher(tmp_path: Path) -> None:
    """Agent should use fetcher when quote_store is not provided."""
    fetcher = DummyFetcher()
    agent = MotivatorAgent(fetcher=fetcher, quote_store=None)

    message = agent.craft_message(user_id="test_user", persona="Steve Jobs")
    #print('*'*80)
    #print(f'message of test_craft_message_without_quote_store_uses_fetcher:  {message}')
    #print('*'*80)
    assert message.text == "Quote from Steve Jobs"
    assert message.source == "dummy"
    assert fetcher.calls == ["Steve Jobs"]


def test_llm_generates_custom_message(tmp_path: Path) -> None:
    quote_store = QuoteStore(tmp_path / "quotes.json")
    quote_store.add([Quote(text="Do or do not.", persona="Yoda", tags=["focus"])])

    profile_store = UserProfileStore(tmp_path / "profiles")
    profile = UserProfile(user_id="padawan", name="Luke", primary_persona="Yoda", study_topics=["Force control"])
    profile_store.save(profile)

    llm = DummyLLM()
    agent = MotivatorAgent(
        fetcher=None,
        profile_store=profile_store,
        quote_store=quote_store,
        llm=llm,
    )

    message = agent.craft_message(user_id="padawan")

    assert "Do or do not." in message.text
    assert "Luke" in message.text
    assert message.source == "quote_store"
    assert llm.calls and llm.calls[0]["persona"] == "Yoda"

"""Tests for quote storage helper."""

from __future__ import annotations

from agents.quote_store import Quote, QuoteStore


def test_add_and_retrieve_quotes(tmp_path) -> None:
    store = QuoteStore(tmp_path / "quotes.json")
    quote_one = Quote(
        text="Stay hungry, stay foolish.",
        persona="Steve Jobs",
        tags=["focus", "innovation"],
        source_url="https://example.com/jobs",
    )
    quote_two = Quote(
        text="Everything negative – pressure, challenges – is an opportunity to rise.",
        persona="Kobe Bryant",
        tags=["perseverance"],
    )

    store.add([quote_one, quote_two])

    jobs_quotes = store.get_by_persona("Steve Jobs")
    assert len(jobs_quotes) == 1
    assert jobs_quotes[0].text == quote_one.text

    perseverance_quotes = store.search_by_tag("perseverance")
    assert len(perseverance_quotes) == 1
    assert perseverance_quotes[0].persona == "Kobe Bryant"


def test_add_deduplicates_by_persona_and_text(tmp_path) -> None:
    store = QuoteStore(tmp_path / "quotes.json")
    quote = Quote(text="Focus wins games.", persona="Kobe Bryant", tags=["focus"])

    store.add([quote])
    store.add([quote])  # duplicate

    all_quotes = store.all()
    assert len(all_quotes) == 1

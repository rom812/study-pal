#!/usr/bin/env python3
"""Utility to seed the quote store from a JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agents.quote_store import Quote, QuoteStore


def load_quotes(seed_path: Path, store_path: Path, persist: bool = True) -> int:
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    quotes = [Quote.model_validate(item) for item in data]

    store = QuoteStore(store_path)
    before_count = len(store.all())
    store.add(quotes, persist=persist)
    after_count = len(store.all())
    return after_count - before_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Load persona quotes into the quote store.")
    parser.add_argument(
        "--seed",
        type=Path,
        default=Path("data/quotes_seed.json"),
        help="Path to the seed JSON file.",
    )
    parser.add_argument(
        "--store",
        type=Path,
        default=Path("data/quotes_store.json"),
        help="Path to the output quote store file.",
    )
    args = parser.parse_args()

    added = load_quotes(args.seed, args.store)
    print(f"Added {added} new quotes to {args.store}.")


if __name__ == "__main__":
    main()

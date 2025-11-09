"""Quote model and storage utilities for the Motivator agent."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from pydantic import AnyUrl, BaseModel, Field


class Quote(BaseModel):
    """A motivational quote attributed to a persona."""

    text: str
    persona: str
    tags: list[str] = Field(default_factory=list)
    source_url: Optional[AnyUrl] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[str] = None

    def normalized_text(self) -> str:
        """Lowercased text used for deduplication."""
        return self.text.strip().lower()


class QuoteStore:
    """JSON-backed cache of persona quotes with simple lookup helpers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._cache: list[Quote] | None = None

    # Internal helpers -------------------------------------------------
    def _load_cache(self) -> list[Quote]:
        if self._cache is None:
            if self.path.exists():
                raw = self.path.read_text(encoding="utf-8").strip()
                if raw:
                    data = json.loads(raw)
                    self._cache = [Quote.model_validate(item) for item in data]
                    return self._cache
            self._cache = []
        return self._cache

    def _persist_cache(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [
            quote.model_dump(mode="json", exclude_none=True) for quote in self._load_cache()
        ]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Public API -------------------------------------------------------
    def all(self) -> list[Quote]:
        """Return all quotes currently cached."""
        return list(self._load_cache())

    def add(self, quotes: Iterable[Quote], persist: bool = True) -> None:
        """Add one or multiple quotes, avoiding duplicates by text/persona."""
        cache = self._load_cache()
        existing_keys = {(quote.persona.lower(), quote.normalized_text()) for quote in cache}

        added_any = False
        for quote in quotes:
            key = (quote.persona.lower(), quote.normalized_text())
            if key not in existing_keys:
                cache.append(quote)
                existing_keys.add(key)
                added_any = True

        if added_any and persist:
            self._persist_cache()

    def get_by_persona(self, persona: str, limit: int | None = None) -> list[Quote]:
        """Return quotes for a specific persona."""
        matches = [quote for quote in self._load_cache() if quote.persona.lower() == persona.lower()]
        return matches[:limit] if limit is not None else matches

    def search_by_tag(
        self,
        tag: str,
        *,
        persona: str | None = None,
        limit: int | None = None,
    ) -> list[Quote]:
        """Return quotes containing the tag, optionally filtering by persona."""
        tag_lower = tag.lower()
        matches = []
        for quote in self._load_cache():
            if persona and quote.persona.lower() != persona.lower():
                continue
            if any(t.lower() == tag_lower for t in quote.tags):
                matches.append(quote)
        return matches[:limit] if limit is not None else matches

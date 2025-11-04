"""LangChain-based retrieval augmented generation pipeline stubs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class RAGPipeline:
    """Coordinates document ingestion and retrieval."""

    embedding_model: str = "text-embedding-3-large"

    def ingest(self, paths: Iterable[Path]) -> None:
        """Load documents and push them through the embedding workflow."""
        # TODO: hook into LangChain loaders and a vector store
        _ = list(paths)

    def run_query(self, query: str) -> list[str]:
        """Return retrieved snippets as part of the RAG cycle."""
        # TODO: integrate with LangChain retrievers
        _ = query
        return ["Stub context snippet"]


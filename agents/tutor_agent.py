"""Tutor agent powers RAG-backed study interactions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from pydantic import BaseModel


class VectorStore(Protocol):
    """Minimal interface for embedding storage."""

    def add_documents(self, docs: Iterable[dict]) -> None:
        ...

    def similarity_search(self, query: str, k: int = 5) -> list[dict]:
        ...


class QuizItem(BaseModel):
    """Structured quiz output validated via Pydantic."""

    question: str
    answer: str
    difficulty: str


@dataclass
class TutorAgent:
    """Transforms study materials into interactive learning prompts."""

    store: VectorStore

    def ingest_material(self, path: Path) -> None:
        """Process a study resource and index it in the vector store."""
        # TODO: implement document parsing and embedding pipeline
        _ = path

    def generate_quiz(self, topic: str) -> list[QuizItem]:
        """Produce quiz items using retrieved context."""
        # TODO: implement RAG-driven quiz creation
        _ = self.store.similarity_search(topic, k=3)
        return [
            QuizItem(
                question=f"Stub question about {topic}?",
                answer="Stub answer",
                difficulty="medium",
            )
        ]


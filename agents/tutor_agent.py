"""Tutor agent powers RAG-backed study interactions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from pydantic import BaseModel

from core.rag_pipeline import RAGPipeline


class VectorStore(Protocol):
    """Minimal interface for embedding storage."""

    def add_documents(self, docs: Iterable[dict]) -> None: ...

    def similarity_search(self, query: str, k: int = 5) -> list[dict]: ...


class QuizItem(BaseModel):
    """Structured quiz output validated via Pydantic."""

    question: str
    answer: str
    difficulty: str


@dataclass
class TutorAgent:
    """
    Transforms study materials into interactive learning prompts.

    Uses RAG (Retrieval Augmented Generation) to:
    - Ingest PDF study materials
    - Generate quizzes based on content
    - Answer questions with context from materials
    """

    rag_pipeline: RAGPipeline

    def ingest_material(self, path: Path) -> int:
        """
        Process a study resource and index it in the vector store.

        Args:
            path: Path to PDF file to ingest

        Returns:
            Number of chunks processed

        Example:
            tutor = TutorAgent(rag_pipeline=RAGPipeline())
            num_chunks = tutor.ingest_material(Path("calculus_notes.pdf"))
            print(f"Ingested {num_chunks} chunks")
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Only PDF files are supported, got: {path.suffix}")

        print(f"[tutor] Ingesting material from {path.name}...")

        # Use RAG pipeline to process the PDF
        num_chunks = self.rag_pipeline.ingest([path])

        print(f"[tutor] Successfully ingested {path.name} ({num_chunks} chunks)")
        return num_chunks

    def generate_quiz(self, topic: str, num_questions: int = 5) -> list[QuizItem]:
        """
        Produce quiz items using retrieved context.

        Args:
            topic: Topic to generate quiz about
            num_questions: Number of questions to generate

        Returns:
            List of QuizItem objects

        Note: This is a stub implementation. Full implementation will be in Phase 3.

        Example:
            quiz = tutor.generate_quiz("derivatives", num_questions=3)
            for item in quiz:
                print(f"Q: {item.question}")
                print(f"A: {item.answer}")
        """
        # Retrieve relevant context
        context = self.rag_pipeline.run_query(topic, k=3)

        # TODO: Phase 3 - Use LLM to generate quiz from context
        # For now, return stub with context-aware message
        if context:
            return [
                QuizItem(
                    question=f"Question about {topic} (context available)",
                    answer="Answer will be generated from context in Phase 3",
                    difficulty="medium",
                )
            ]
        else:
            return [
                QuizItem(
                    question=f"No context found for {topic}",
                    answer="Please ingest study materials first",
                    difficulty="easy",
                )
            ]

    def get_context(self, query: str, k: int = 3) -> list[str]:
        """
        Retrieve relevant context for a query.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of relevant text snippets

        Example:
            context = tutor.get_context("What is a derivative?")
            for snippet in context:
                print(snippet)
        """
        return self.rag_pipeline.run_query(query, k=k)

    def count_materials(self) -> int:
        """
        Get the number of document chunks in the knowledge base.

        Returns:
            Number of chunks stored
        """
        return self.rag_pipeline.count_documents()

    def clear_materials(self) -> None:
        """Clear all ingested materials from the knowledge base."""
        print("[tutor] Clearing all materials...")
        self.rag_pipeline.clear()
        print("[tutor] Materials cleared")

"""Stub tests for TutorAgent."""

from pathlib import Path

from agents.tutor_agent import QuizItem, TutorAgent


class DummyVectorStore:
    def add_documents(self, docs):
        self.docs = list(docs)

    def similarity_search(self, query: str, k: int = 5):
        return [{"content": f"Context for {query}"} for _ in range(k)]


def test_generate_quiz_returns_items():
    agent = TutorAgent(store=DummyVectorStore())

    quiz = agent.generate_quiz("derivatives")

    assert all(isinstance(item, QuizItem) for item in quiz)
    assert quiz[0].question.startswith("Stub question")


def test_ingest_material_accepts_path(tmp_path: Path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text("calculus notes")

    agent = TutorAgent(store=DummyVectorStore())
    agent.ingest_material(file_path)

    # Stub implementation does nothing yet but should not raise
    assert True


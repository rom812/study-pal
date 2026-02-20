"""Tests for TutorAgent - high-level RAG-powered tutoring interface."""

from pathlib import Path

import pytest

from agents.tutor_agent import QuizItem, TutorAgent
from core.rag_pipeline import RAGPipeline


@pytest.fixture
def test_pdf():
    """Get path to test PDF fixture."""
    return Path(__file__).parent / "fixtures" / "calculus_sample.pdf"


@pytest.fixture
def tutor_agent(tmp_path):
    """Create a TutorAgent with temporary storage."""
    pipeline = RAGPipeline(collection_name="test_tutor", persist_directory=tmp_path / "tutor_test")
    return TutorAgent(rag_pipeline=pipeline)


def test_ingest_material_success(tutor_agent, test_pdf):
    """Test successful PDF ingestion."""
    num_chunks = tutor_agent.ingest_material(test_pdf)

    assert num_chunks > 0
    assert tutor_agent.count_materials() == num_chunks


def test_ingest_material_nonexistent_file(tutor_agent, tmp_path):
    """Test ingesting non-existent file raises error."""
    fake_path = tmp_path / "nonexistent.pdf"

    with pytest.raises(FileNotFoundError):
        tutor_agent.ingest_material(fake_path)


def test_ingest_material_wrong_file_type(tutor_agent, tmp_path):
    """Test ingesting non-PDF file raises error."""
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Some notes")

    with pytest.raises(ValueError, match="Only PDF files are supported"):
        tutor_agent.ingest_material(txt_file)


def test_get_context(tutor_agent, test_pdf):
    """Test retrieving context for a query."""
    tutor_agent.ingest_material(test_pdf)

    context = tutor_agent.get_context("What is a derivative?", k=3)

    assert len(context) <= 3
    assert all(isinstance(snippet, str) for snippet in context)

    # Should contain relevant content
    all_content = " ".join(context).lower()
    assert "derivative" in all_content


def test_get_context_different_k_values(tutor_agent, test_pdf):
    """Test k parameter controls number of context snippets."""
    tutor_agent.ingest_material(test_pdf)

    context_2 = tutor_agent.get_context("integrals", k=2)
    context_5 = tutor_agent.get_context("integrals", k=5)

    assert len(context_2) <= 2
    assert len(context_5) <= 5


def test_count_materials(tutor_agent, test_pdf):
    """Test counting ingested materials."""
    assert tutor_agent.count_materials() == 0

    tutor_agent.ingest_material(test_pdf)

    assert tutor_agent.count_materials() > 0


def test_clear_materials(tutor_agent, test_pdf):
    """Test clearing all materials."""
    tutor_agent.ingest_material(test_pdf)
    assert tutor_agent.count_materials() > 0

    tutor_agent.clear_materials()

    assert tutor_agent.count_materials() == 0


def test_generate_quiz_returns_items(tutor_agent, test_pdf):
    """Test quiz generation (stub implementation)."""
    tutor_agent.ingest_material(test_pdf)

    quiz = tutor_agent.generate_quiz("derivatives")

    assert all(isinstance(item, QuizItem) for item in quiz)
    # Stub implementation returns context-aware message
    assert "context available" in quiz[0].question or "No context found" in quiz[0].question


def test_generate_quiz_without_materials(tutor_agent):
    """Test quiz generation without ingested materials."""
    quiz = tutor_agent.generate_quiz("derivatives")

    assert all(isinstance(item, QuizItem) for item in quiz)
    # Without materials, should indicate no context
    assert "No context found" in quiz[0].question or "context" in quiz[0].question.lower()


def test_multiple_material_ingestion(tutor_agent, test_pdf):
    """Test ingesting materials multiple times."""
    chunks1 = tutor_agent.ingest_material(test_pdf)
    total_before = tutor_agent.count_materials()

    # Ingest again (same file)
    chunks2 = tutor_agent.ingest_material(test_pdf)
    total_after = tutor_agent.count_materials()

    # Should accumulate
    assert total_after == total_before + chunks2
    assert chunks1 == chunks2  # Same file produces same chunks


def test_context_relevance(tutor_agent, test_pdf):
    """Test that context retrieval returns relevant content for specific topics."""
    tutor_agent.ingest_material(test_pdf)

    # Query about derivatives
    derivative_context = tutor_agent.get_context("derivative rate of change", k=2)
    derivative_text = " ".join(derivative_context).lower()

    # Query about integrals
    integral_context = tutor_agent.get_context("integral area under curve", k=2)
    integral_text = " ".join(integral_context).lower()

    # Each should contain relevant keywords
    assert "derivative" in derivative_text or "rate" in derivative_text
    assert "integral" in integral_text or "area" in integral_text

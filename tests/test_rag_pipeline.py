"""Tests for RAGPipeline - end-to-end document ingestion and retrieval."""

from pathlib import Path

import pytest

from core.rag_pipeline import RAGPipeline


@pytest.fixture
def test_pdf():
    """Get path to test PDF fixture."""
    return Path(__file__).parent / "fixtures" / "calculus_sample.pdf"


@pytest.fixture
def pipeline(tmp_path):
    """Create a RAG pipeline with temporary storage."""
    return RAGPipeline(collection_name="test_collection", persist_directory=tmp_path / "chroma_test")


def test_pipeline_initialization(pipeline):
    """Test RAG pipeline initializes correctly."""
    assert pipeline.embedding_model == "text-embedding-3-large"
    assert pipeline.collection_name == "test_collection"
    assert pipeline.embeddings is not None
    assert pipeline.document_processor is not None
    assert pipeline.vector_store is not None


def test_ingest_pdf_success(pipeline, test_pdf):
    """Test successful PDF ingestion."""
    num_chunks = pipeline.ingest([test_pdf])

    assert num_chunks > 0
    assert pipeline.count_documents() == num_chunks


def test_ingest_multiple_pdfs(pipeline, test_pdf):
    """Test ingesting multiple PDFs."""
    # Ingest same PDF twice to simulate multiple files
    num_chunks = pipeline.ingest([test_pdf, test_pdf])

    assert num_chunks > 0
    # Should have chunks from both files
    assert pipeline.count_documents() == num_chunks


def test_ingest_nonexistent_file(pipeline, tmp_path):
    """Test ingesting non-existent file raises error."""
    fake_path = tmp_path / "nonexistent.pdf"

    with pytest.raises(FileNotFoundError):
        pipeline.ingest([fake_path])


def test_run_query_returns_relevant_results(pipeline, test_pdf):
    """Test query returns relevant content."""
    # Ingest the calculus PDF
    pipeline.ingest([test_pdf])

    # Query about derivatives
    results = pipeline.run_query("What is a derivative?", k=3)

    assert len(results) <= 3
    assert all(isinstance(result, str) for result in results)

    # Results should contain relevant content
    all_content = " ".join(results).lower()
    assert "derivative" in all_content


def test_run_query_different_topics(pipeline, test_pdf):
    """Test queries for different topics return appropriate content."""
    pipeline.ingest([test_pdf])

    # Query about integrals
    integral_results = pipeline.run_query("Tell me about integrals", k=2)
    integral_content = " ".join(integral_results).lower()

    # Query about limits
    limit_results = pipeline.run_query("What are limits?", k=2)
    limit_content = " ".join(limit_results).lower()

    # Should find relevant content for each topic
    assert "integral" in integral_content or "area" in integral_content
    assert "limit" in limit_content


def test_run_query_k_parameter(pipeline, test_pdf):
    """Test k parameter controls number of results."""
    pipeline.ingest([test_pdf])

    results_3 = pipeline.run_query("calculus", k=3)
    results_5 = pipeline.run_query("calculus", k=5)

    assert len(results_3) <= 3
    assert len(results_5) <= 5


def test_run_query_with_scores(pipeline, test_pdf):
    """Test query with similarity scores."""
    pipeline.ingest([test_pdf])

    results = pipeline.run_query_with_scores("derivative", k=3)

    assert len(results) <= 3
    for content, score in results:
        assert isinstance(content, str)
        assert isinstance(score, float)
        assert score >= 0  # Scores should be non-negative


def test_count_documents(pipeline, test_pdf):
    """Test document counting."""
    assert pipeline.count_documents() == 0

    pipeline.ingest([test_pdf])

    count = pipeline.count_documents()
    assert count > 0


def test_clear_pipeline(pipeline, test_pdf):
    """Test clearing all documents."""
    pipeline.ingest([test_pdf])
    assert pipeline.count_documents() > 0

    pipeline.clear()

    assert pipeline.count_documents() == 0


def test_persistence(tmp_path, test_pdf):
    """Test that documents persist between pipeline instances."""
    persist_dir = tmp_path / "persist_test"

    # Create pipeline and ingest
    pipeline1 = RAGPipeline(collection_name="persist_test", persist_directory=persist_dir)
    num_chunks = pipeline1.ingest([test_pdf])

    # Create new pipeline instance with same directory
    pipeline2 = RAGPipeline(collection_name="persist_test", persist_directory=persist_dir)

    # Should have same documents
    assert pipeline2.count_documents() == num_chunks

    # Should be able to query
    results = pipeline2.run_query("derivative", k=2)
    assert len(results) > 0


def test_get_retriever(pipeline, test_pdf):
    """Test getting a LangChain retriever."""
    pipeline.ingest([test_pdf])

    retriever = pipeline.get_retriever(k=3)

    assert retriever is not None

    # Test retriever works (using invoke API)
    docs = retriever.invoke("What is a derivative?")
    assert len(docs) > 0

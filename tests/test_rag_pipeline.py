"""Stub tests for RAGPipeline."""

from pathlib import Path

from core.rag_pipeline import RAGPipeline


def test_ingest_handles_iterable(tmp_path: Path):
    paths = [tmp_path / "doc.txt"]
    paths[0].write_text("study guide")

    pipeline = RAGPipeline()
    pipeline.ingest(paths)

    assert True  # No exceptions for stub implementation


def test_run_query_returns_stub():
    pipeline = RAGPipeline()

    results = pipeline.run_query("integration by parts")

    assert results == ["Stub context snippet"]


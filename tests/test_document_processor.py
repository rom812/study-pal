"""Tests for DocumentProcessor - PDF loading and chunking."""

from pathlib import Path

import pytest
from langchain_core.documents import Document

from core.document_processor import DocumentProcessor


@pytest.fixture
def processor():
    """Create a DocumentProcessor with default settings."""
    return DocumentProcessor(chunk_size=1000, chunk_overlap=200)


@pytest.fixture
def test_pdf():
    """Get path to test PDF fixture."""
    return Path(__file__).parent / "fixtures" / "calculus_sample.pdf"


def test_load_pdf_success(processor, test_pdf):
    """Test successful PDF loading."""
    documents = processor.load_pdf(test_pdf)

    assert len(documents) > 0
    assert all(isinstance(doc, Document) for doc in documents)

    # Check metadata is added
    assert documents[0].metadata["source_file"] == "calculus_sample.pdf"
    assert "source_path" in documents[0].metadata

    # Check content was extracted
    content = documents[0].page_content
    assert "Calculus" in content or "derivative" in content.lower()


def test_load_pdf_file_not_found(processor):
    """Test loading non-existent PDF raises error."""
    with pytest.raises(FileNotFoundError):
        processor.load_pdf(Path("nonexistent.pdf"))


def test_load_pdf_wrong_extension(processor, tmp_path):
    """Test loading non-PDF file raises error."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Not a PDF")

    with pytest.raises(ValueError, match="must be a PDF"):
        processor.load_pdf(txt_file)


def test_chunk_documents(processor):
    """Test document chunking."""
    # Create a large document
    large_text = "This is a test sentence. " * 100  # ~2500 chars
    documents = [Document(page_content=large_text, metadata={"page": 1})]

    chunks = processor.chunk_documents(documents)

    assert len(chunks) > 1  # Should be split

    # Check all chunks have metadata
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_index"] == i
        assert chunk.metadata["chunk_size"] == len(chunk.page_content)
        assert chunk.metadata["page"] == 1  # Original metadata preserved


def test_chunk_documents_empty_list(processor):
    """Test chunking empty list returns empty list."""
    chunks = processor.chunk_documents([])
    assert chunks == []


def test_chunk_documents_preserves_small_docs(processor):
    """Test small documents don't get unnecessarily split."""
    small_text = "Short document."
    documents = [Document(page_content=small_text, metadata={"source": "test"})]

    chunks = processor.chunk_documents(documents)

    assert len(chunks) == 1
    assert chunks[0].page_content == small_text
    assert chunks[0].metadata["source"] == "test"


def test_extract_metadata(processor):
    """Test metadata extraction."""
    doc = Document(page_content="Test content with multiple words here.", metadata={"page": 5, "source": "test.pdf"})

    metadata = processor.extract_metadata(doc)

    assert metadata["content_length"] == len(doc.page_content)
    assert metadata["word_count"] == 6
    assert metadata["page_number"] == 5
    assert metadata["source"] == "test.pdf"


def test_process_pdf_end_to_end(processor, test_pdf):
    """Test complete PDF processing pipeline."""
    chunks = processor.process_pdf(test_pdf)

    # Should produce chunks
    assert len(chunks) > 0

    # All chunks should have required metadata
    for chunk in chunks:
        assert "source_file" in chunk.metadata
        assert "chunk_index" in chunk.metadata
        assert "chunk_size" in chunk.metadata
        assert chunk.metadata["source_file"] == "calculus_sample.pdf"

    # Content should be from the PDF
    all_content = " ".join(chunk.page_content for chunk in chunks)
    assert any(keyword in all_content.lower() for keyword in ["derivative", "integral", "limit", "calculus"])


def test_chunk_size_configuration():
    """Test custom chunk size configuration."""
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)

    large_text = "Word " * 200  # ~1000 chars
    documents = [Document(page_content=large_text)]

    chunks = processor.chunk_documents(documents)

    # With smaller chunk size, should get more chunks
    assert len(chunks) > 5

    # Each chunk should be roughly around chunk_size
    for chunk in chunks[:-1]:  # Excluding last chunk which may be smaller
        assert len(chunk.page_content) <= 120  # chunk_size + some buffer

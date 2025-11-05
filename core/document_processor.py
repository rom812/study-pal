"""Document processing for RAG pipeline - loading and chunking documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


class DocumentProcessor:
    """Handles document loading, chunking, and metadata extraction."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """
        Initialize the document processor.

        Args:
            chunk_size: Target size for each chunk in characters (~250 words)
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def load_pdf(self, path: Path) -> list[Document]:
        """
        Load a PDF document and extract its content.

        Args:
            path: Path to the PDF file

        Returns:
            List of Document objects (one per page)

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF, got: {path.suffix}")

        try:
            loader = PyPDFLoader(str(path))
            documents = loader.load()

            # Add source metadata
            for doc in documents:
                doc.metadata["source_file"] = path.name
                doc.metadata["source_path"] = str(path)

            return documents

        except Exception as e:
            raise ValueError(f"Failed to load PDF {path}: {e}") from e

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """
        Split documents into smaller chunks for embedding.

        Args:
            documents: List of documents to chunk

        Returns:
            List of chunked documents with preserved metadata
        """
        if not documents:
            return []

        chunks = self.text_splitter.split_documents(documents)

        # Add chunk index to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_size"] = len(chunk.page_content)

        return chunks

    def extract_metadata(self, document: Document) -> dict[str, Any]:
        """
        Extract and enrich metadata from a document.

        Args:
            document: Document to extract metadata from

        Returns:
            Dictionary of metadata
        """
        metadata = document.metadata.copy()

        # Add content statistics
        content = document.page_content
        metadata["content_length"] = len(content)
        metadata["word_count"] = len(content.split())

        # Add page information if available
        if "page" in metadata:
            metadata["page_number"] = metadata["page"]

        return metadata

    def process_pdf(self, path: Path) -> list[Document]:
        """
        Complete processing pipeline: load PDF and chunk it.

        Args:
            path: Path to PDF file

        Returns:
            List of chunked documents ready for embedding

        Example:
            processor = DocumentProcessor()
            chunks = processor.process_pdf(Path("lecture_notes.pdf"))
            # Returns ~50 chunks from a 50-page document
        """
        documents = self.load_pdf(path)
        chunks = self.chunk_documents(documents)

        print(f"[document_processor] Processed {path.name}:")
        print(f"  - Pages: {len(documents)}")
        print(f"  - Chunks: {len(chunks)}")
        print(f"  - Avg chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars")

        return chunks

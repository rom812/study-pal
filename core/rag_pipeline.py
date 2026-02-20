"""LangChain-based retrieval augmented generation pipeline."""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings

from .document_processor import DocumentProcessor
from .vector_stores import ChromaVectorStore

# Global singleton instances (one per user) with thread safety
_rag_pipeline_instances: dict[str, RAGPipeline] = {}
_rag_pipeline_lock = threading.Lock()


@dataclass
class RAGPipeline:
    """
    Coordinates document ingestion and retrieval for RAG applications.

    Handles the complete pipeline from PDF files to semantic search:
    1. Load PDFs using DocumentProcessor
    2. Chunk documents into manageable pieces
    3. Generate embeddings using OpenAI
    4. Store in ChromaDB vector store
    5. Provide semantic search and retrieval
    """

    embedding_model: str = "text-embedding-3-small"
    collection_name: str = "study_materials"
    persist_directory: Path = field(default_factory=lambda: Path("data/chroma_db"))
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # These will be initialized in __post_init__
    document_processor: DocumentProcessor = field(init=False)
    vector_store: ChromaVectorStore = field(init=False)
    embeddings: OpenAIEmbeddings = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the pipeline components."""
        # Initialize OpenAI embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=api_key,
        )

        # Initialize document processor
        self.document_processor = DocumentProcessor(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        # Initialize vector store
        self.vector_store = ChromaVectorStore(
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

        print(f"[rag_pipeline] Initialized for collection: {self.collection_name}")

    def ingest(self, paths: Iterable[Path]) -> int:
        """
        Load documents and push them through the embedding workflow.

        Args:
            paths: Iterable of Path objects pointing to PDF files

        Returns:
            Number of chunks processed and stored

        Example:
            pipeline = RAGPipeline()
            num_chunks = pipeline.ingest([
                Path("lecture1.pdf"),
                Path("lecture2.pdf")
            ])
            print(f"Processed {num_chunks} chunks")
        """
        paths_list = list(paths)

        if not paths_list:
            print("[rag_pipeline] No paths provided")
            return 0

        all_chunks = []

        for path in paths_list:
            try:
                # Process PDF into chunks
                chunks = self.document_processor.process_pdf(path)
                all_chunks.extend(chunks)

            except (FileNotFoundError, ValueError):
                # Re-raise critical errors
                raise
            except Exception as e:
                print(f"[rag_pipeline] Error processing {path}: {e}")
                continue

        if not all_chunks:
            print("[rag_pipeline] No chunks to ingest")
            return 0

        # Add chunks to vector store
        self.vector_store.add_documents(all_chunks)

        print(f"[rag_pipeline] Successfully ingested {len(all_chunks)} chunks from {len(paths_list)} files")
        return len(all_chunks)

    def run_query(self, query: str, k: int = 5) -> list[str]:
        """
        Return retrieved snippets as part of the RAG cycle.

        Args:
            query: Query text to search for
            k: Number of results to return

        Returns:
            List of content strings from the most relevant chunks

        Example:
            pipeline = RAGPipeline()
            results = pipeline.run_query("What is calculus?", k=3)
            for result in results:
                print(result)
        """
        results = self.vector_store.similarity_search(query, k=k)

        # Log search results
        if results:
            print(f"[rag_pipeline] ✓ Found context: {len(results)} chunks retrieved")
        else:
            print("[rag_pipeline] ✗ No context found for query")

        return [result["content"] for result in results]

    def run_query_with_scores(
        self,
        query: str,
        k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        Retrieve documents with similarity scores.

        Args:
            query: Query text
            k: Number of results

        Returns:
            List of tuples (content, score)
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)

        return [(result["content"], score) for result, score in results]

    def get_retriever(
        self,
        search_type: str = "similarity",
        k: int = 5,
    ) -> BaseRetriever:
        """
        Get a LangChain retriever for use with chains.

        Args:
            search_type: Type of search ("similarity", "mmr")
            k: Number of documents to retrieve

        Returns:
            LangChain BaseRetriever

        Example:
            retriever = pipeline.get_retriever(k=3)
            qa_chain = RetrievalQA.from_chain_type(
                llm=ChatOpenAI(),
                retriever=retriever
            )
        """
        return self.vector_store.get_retriever(
            search_type=search_type,
            search_kwargs={"k": k},
        )

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.vector_store.clear()

    def count_documents(self) -> int:
        """Get the number of documents in the vector store."""
        return self.vector_store.count_documents()


def _sanitize_collection_name(user_id: str) -> str:
    """
    Sanitize user_id to create a valid ChromaDB collection name.

    ChromaDB requirements:
    - Must start and end with alphanumeric characters [a-zA-Z0-9]
    - Can contain [a-zA-Z0-9._-]
    - Must be 3-512 characters long

    Args:
        user_id: Raw user identifier

    Returns:
        Valid ChromaDB collection name

    Example:
        >>> _sanitize_collection_name("test_user")
        'materials-test-user'
        >>> _sanitize_collection_name("123user")
        'materials-user123'
        >>> _sanitize_collection_name("user@domain.com")
        'materials-userdomain.com'
    """
    import re

    # Replace invalid characters with hyphens
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "-", user_id)

    # Remove leading/trailing invalid characters
    sanitized = re.sub(r"^[^a-zA-Z0-9]+", "", sanitized)
    sanitized = re.sub(r"[^a-zA-Z0-9]+$", "", sanitized)

    # If empty after sanitization, use default
    if not sanitized:
        sanitized = "default"

    # Build collection name: materials-{user_id}
    # Using hyphen instead of underscore to avoid double underscore issues
    collection_name = f"materials-{sanitized}"

    # Ensure minimum length of 3 characters
    if len(collection_name) < 3:
        collection_name = f"materials-{sanitized}00"

    # Ensure maximum length of 512 characters
    if len(collection_name) > 512:
        collection_name = collection_name[:512]
        # Make sure it still ends with alphanumeric
        collection_name = re.sub(r"[^a-zA-Z0-9]+$", "", collection_name)

    return collection_name


def get_rag_pipeline(user_id: str = "default_user") -> RAGPipeline:
    """
    Get or create a user-specific RAG pipeline instance.

    Each user gets their own isolated ChromaDB collection, ensuring that
    study materials don't mix between users. This provides:
    - Data isolation: Users only see their own materials
    - Better performance: Smaller collections = faster searches
    - Clean user experience: No cross-contamination of content

    Args:
        user_id: User identifier (defaults to "default_user")

    Returns:
        User-specific RAGPipeline instance

    Example:
        # Get pipeline for specific user
        pipeline = get_rag_pipeline(user_id="alice")
        results = pipeline.run_query("What is calculus?")

        # Different user gets different pipeline
        pipeline2 = get_rag_pipeline(user_id="bob")
        # alice and bob have separate collections
    """
    global _rag_pipeline_instances

    with _rag_pipeline_lock:
        if user_id not in _rag_pipeline_instances:
            print(f"[rag_pipeline] Creating pipeline for user: {user_id}")
            # Create user-specific collection name (sanitized for ChromaDB)
            collection_name = _sanitize_collection_name(user_id)
            _rag_pipeline_instances[user_id] = RAGPipeline(collection_name=collection_name)

        return _rag_pipeline_instances[user_id]


def reset_rag_pipeline(user_id: str | None = None) -> None:
    """
    Reset RAG pipeline instance(s).

    Args:
        user_id: If provided, resets only that user's pipeline.
                 If None, resets all pipelines.

    Example:
        # Reset specific user
        reset_rag_pipeline(user_id="alice")

        # Reset all users (for testing)
        reset_rag_pipeline()
    """
    global _rag_pipeline_instances

    if user_id is None:
        # Reset all instances
        _rag_pipeline_instances.clear()
        print("[rag_pipeline] All pipeline instances reset")
    else:
        # Reset specific user
        if user_id in _rag_pipeline_instances:
            del _rag_pipeline_instances[user_id]
            print(f"[rag_pipeline] Pipeline instance reset for user: {user_id}")
        else:
            print(f"[rag_pipeline] No pipeline instance found for user: {user_id}")

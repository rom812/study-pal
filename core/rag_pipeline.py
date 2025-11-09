"""LangChain-based retrieval augmented generation pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings

from .document_processor import DocumentProcessor
from .vector_stores import ChromaVectorStore


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

        print(f"[rag_pipeline] Initialized with embedding model: {self.embedding_model}")
        print(f"[rag_pipeline] Chunk size: {self.chunk_size}, overlap: {self.chunk_overlap}")

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

            except (FileNotFoundError, ValueError) as e:
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


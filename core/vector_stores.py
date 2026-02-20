"""Vector store implementations for RAG pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever


class ChromaVectorStore:
    """
    ChromaDB-based vector store implementation.

    Provides persistent storage for document embeddings with semantic search capabilities.
    """

    def __init__(
        self,
        collection_name: str,
        persist_directory: Path,
        embedding_function: Embeddings,
    ) -> None:
        """
        Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the collection (e.g., "study_materials")
            persist_directory: Directory to persist the database
            embedding_function: Embedding model to use (e.g., OpenAIEmbeddings)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function

        # Create persist directory if it doesn't exist
        persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
                persist_directory=str(persist_directory),
            ),
        )

        # Initialize LangChain Chroma wrapper
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=embedding_function,
        )

        print(f"[vector_store] Initialized collection: {collection_name}")

    def add_documents(self, docs: Iterable[dict | Document]) -> list[str]:
        """
        Add documents to the vector store.

        Args:
            docs: Iterable of documents (dict or Document objects)

        Returns:
            List of document IDs

        Example:
            ids = store.add_documents([
                {"page_content": "Text...", "metadata": {...}},
                Document(page_content="Text...", metadata={...})
            ])
        """
        # Convert dicts to Documents if needed
        documents = []
        for doc in docs:
            if isinstance(doc, dict):
                documents.append(
                    Document(
                        page_content=doc.get("page_content", doc.get("content", "")),
                        metadata=doc.get("metadata", {}),
                    )
                )
            else:
                documents.append(doc)

        if not documents:
            return []

        # Add to vector store
        ids = self.vector_store.add_documents(documents)

        print(f"[vector_store] Added {len(documents)} documents")
        return ids

    def similarity_search(
        self,
        query: str,
        k: int = 5,
    ) -> list[dict]:
        """
        Search for similar documents using semantic similarity.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of dicts with 'content' and 'metadata' keys

        Example:
            results = store.similarity_search("What is calculus?", k=3)
            for result in results:
                print(result['content'])
        """
        documents = self.vector_store.similarity_search(query, k=k)

        # Convert to dict format
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in documents
        ]

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 5,
    ) -> list[tuple[dict, float]]:
        """
        Search with similarity scores.

        Args:
            query: Query text
            k: Number of results

        Returns:
            List of tuples (dict, score) where lower score = more similar
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)

        return [
            (
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                },
                float(score),
            )
            for doc, score in results
        ]

    def get_retriever(
        self,
        search_type: str = "similarity",
        search_kwargs: dict | None = None,
    ) -> BaseRetriever:
        """
        Get a retriever for use with LangChain chains.

        Args:
            search_type: Type of search ("similarity", "mmr", "similarity_score_threshold")
            search_kwargs: Additional search parameters (e.g., {"k": 5})

        Returns:
            LangChain BaseRetriever

        Example:
            retriever = store.get_retriever(search_kwargs={"k": 3})
            docs = retriever.get_relevant_documents("query")
        """
        if search_kwargs is None:
            search_kwargs = {"k": 5}

        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def delete_collection(self) -> None:
        """
        Delete the collection and all its documents.

        Warning: This is irreversible!
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"[vector_store] Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"[vector_store] Error deleting collection: {e}")

    def count_documents(self) -> int:
        """
        Get the number of documents in the collection.

        Returns:
            Number of documents
        """
        try:
            collection = self.client.get_collection(name=self.collection_name)
            return collection.count()
        except Exception:
            return 0

    def clear(self) -> None:
        """Clear all documents from the collection without deleting it."""
        self.delete_collection()
        # Recreate the collection
        self.vector_store = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
        )
        print(f"[vector_store] Cleared collection: {self.collection_name}")

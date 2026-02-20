"""Shared pytest fixtures for Study Pal tests."""

import os
from unittest.mock import MagicMock, patch

import pytest


# Create mock embeddings instance that handles multiple documents
def _create_mock_embeddings(texts):
    """Generate mock embeddings for a list of texts."""
    return [[0.1 * (i + 1)] * 3072 for i in range(len(texts))]


_mock_embeddings = MagicMock()
_mock_embeddings.embed_documents.side_effect = _create_mock_embeddings
_mock_embeddings.embed_query.return_value = [0.1] * 3072


# Patch at module level
_embeddings_patcher = patch("langchain_openai.OpenAIEmbeddings", return_value=_mock_embeddings)
_embeddings_patcher.start()


@pytest.fixture(autouse=True, scope="session")
def setup_test_env():
    """Set up test environment."""
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"
    yield
    # Cleanup
    _embeddings_patcher.stop()


# TODO: add fixtures for vector stores, MCP stubs, configuration, etc.

"""Dependency providers for the API layer.

Everything the endpoints need is injected through these functions so tests
can override them via ``app.dependency_overrides``.
"""

from pathlib import Path

from fastapi import Depends
from qdrant_client import QdrantClient

from ai.provider import AIProvider, GeminiProvider
from config.settings import get_settings
from embeddings.cache import EmbeddingCache
from embeddings.provider import EmbeddingProvider, GeminiEmbeddingProvider
from services.ai_service import AIService
from services.repository_service import RepositoryService

#: Persistent embedding cache shared by API indexing runs.
EMBEDDING_CACHE_PATH = (
    Path(__file__).resolve().parent.parent / ".cache" / "embeddings.json"
)


def get_embedding_provider() -> EmbeddingProvider:
    """The embedding provider used for indexing (Gemini by default)."""
    return GeminiEmbeddingProvider()


def get_qdrant_client() -> QdrantClient:
    """Qdrant client pointed at the configured server."""
    return QdrantClient(url=get_settings().qdrant_url)


def get_embedding_cache() -> EmbeddingCache:
    """File-backed embedding cache so re-indexing skips unchanged chunks."""
    return EmbeddingCache(EMBEDDING_CACHE_PATH)


def get_repository_service(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_cache: EmbeddingCache = Depends(get_embedding_cache),
) -> RepositoryService:
    """The fully wired repository orchestration service."""
    return RepositoryService(embedding_provider, qdrant_client, embedding_cache)


def get_ai_provider() -> AIProvider:
    """The answer-generation provider (Gemini 2.5 Flash by default)."""
    return GeminiProvider()


def get_ai_service(
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider),
    ai_provider: AIProvider = Depends(get_ai_provider),
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
) -> AIService:
    """The fully wired question-answering service."""
    return AIService(embedding_provider, ai_provider, qdrant_client)

"""Semantic retriever: embeds a query and searches Qdrant."""

import logging
from abc import ABC, abstractmethod

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from chunking.models import ChunkType
from config.settings import get_settings
from embeddings.provider import EmbeddingProvider
from retrieval.models import ChunkPayload, RetrievalResult, RetrievedChunk
from scanner.language import ProgrammingLanguage

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 10


class Retriever(ABC):
    """Retrieves relevant chunks for a natural language query."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float | None = None,
        language: ProgrammingLanguage | str | None = None,
        chunk_type: ChunkType | str | None = None,
        relative_path: str | None = None,
    ) -> RetrievalResult:
        """Return the most similar chunks, best first."""
        raise NotImplementedError


class SemanticRetriever(Retriever):
    """Vector-similarity retrieval over one Qdrant collection.

    Embeds the query with the configured EmbeddingProvider and returns the
    top K hits ordered by similarity. No reranking, no LLM.
    """

    def __init__(
        self,
        provider: EmbeddingProvider,
        collection_name: str,
        client: QdrantClient | None = None,
    ) -> None:
        self._provider = provider
        self._collection = collection_name
        if client is None:
            client = QdrantClient(url=get_settings().qdrant_url)
        self._client = client

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        score_threshold: float | None = None,
        language: ProgrammingLanguage | str | None = None,
        chunk_type: ChunkType | str | None = None,
        relative_path: str | None = None,
    ) -> RetrievalResult:
        """Embed the query and return the top K similar chunks."""
        if not self._client.collection_exists(self._collection):
            logger.warning(
                "Collection %s does not exist; returning empty result",
                self._collection,
            )
            return RetrievalResult(
                query=query,
                collection_name=self._collection,
                top_k=top_k,
                chunks=[],
            )

        [query_vector] = self._provider.embed_batch([query])
        query_filter = _build_filter(language, chunk_type, relative_path)

        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
            score_threshold=score_threshold,
            with_payload=True,
        )

        chunks = [
            RetrievedChunk(
                chunk_id=point.payload["chunk_id"],
                score=point.score,
                repository_name=point.payload["repository_name"],
                chunk=ChunkPayload.model_validate(point.payload),
            )
            for point in response.points
        ]
        logger.info(
            "Query %r -> %d hits (top_k=%d, threshold=%s)",
            query,
            len(chunks),
            top_k,
            score_threshold,
        )
        return RetrievalResult(
            query=query,
            collection_name=self._collection,
            top_k=top_k,
            chunks=chunks,
        )


def _build_filter(
    language: ProgrammingLanguage | str | None,
    chunk_type: ChunkType | str | None,
    relative_path: str | None,
) -> Filter | None:
    """Build a Qdrant payload filter from the optional criteria."""
    conditions: list[FieldCondition] = []
    if language is not None:
        value = (
            language.value if isinstance(language, ProgrammingLanguage) else language
        )
        conditions.append(FieldCondition(key="language", match=MatchValue(value=value)))
    if chunk_type is not None:
        value = chunk_type.value if isinstance(chunk_type, ChunkType) else chunk_type
        conditions.append(
            FieldCondition(key="chunk_type", match=MatchValue(value=value))
        )
    if relative_path is not None:
        conditions.append(
            FieldCondition(key="relative_path", match=MatchValue(value=relative_path))
        )
    if not conditions:
        return None
    return Filter(must=conditions)

"""IndexBuilder: embeds all chunks and writes them to Qdrant."""

import logging
import re
import time
from collections.abc import Callable

from chunking.models import Chunk, RepositoryChunks
from embeddings.cache import EmbeddingCache
from embeddings.models import IndexedRepository, IndexStatistics
from embeddings.provider import EmbeddingProvider
from embeddings.store import QdrantVectorStore

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0


class IndexBuilder:
    """Embeds RepositoryChunks and indexes them into Qdrant.

    Batches requests, retries transient provider failures with exponential
    backoff, and skips chunks whose embedding is already cached. A batch that
    keeps failing is counted as failed and does not abort the run.
    """

    def __init__(
        self,
        provider: EmbeddingProvider,
        store: QdrantVectorStore,
        cache: EmbeddingCache | None = None,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._provider = provider
        self._store = store
        self._cache = cache
        self._batch_size = batch_size
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep

    def build(
        self,
        repository_chunks: RepositoryChunks,
        collection_name: str | None = None,
    ) -> IndexedRepository:
        """Embed every chunk and upsert the results into Qdrant."""
        start = time.perf_counter()
        collection = collection_name or default_collection_name(
            repository_chunks.repository_name
        )
        self._store.ensure_collection(collection, self._provider.dimension)

        ready: list[tuple[Chunk, list[float]]] = []
        pending: list[Chunk] = []
        cached_count = 0
        for chunk in repository_chunks.chunks:
            vector = (
                self._cache.get(EmbeddingCache.key_for(chunk))
                if self._cache is not None
                else None
            )
            if vector is not None:
                ready.append((chunk, vector))
                cached_count += 1
            else:
                pending.append(chunk)

        embedded_count = 0
        failed_count = 0
        for batch_start in range(0, len(pending), self._batch_size):
            batch = pending[batch_start : batch_start + self._batch_size]
            try:
                vectors = self._embed_with_retry([c.content for c in batch])
            except Exception as exc:
                failed_count += len(batch)
                logger.error(
                    "Batch of %d chunks failed permanently: %s", len(batch), exc
                )
                continue
            for chunk, vector in zip(batch, vectors, strict=True):
                ready.append((chunk, vector))
                if self._cache is not None:
                    self._cache.set(EmbeddingCache.key_for(chunk), vector)
            embedded_count += len(batch)

        if self._cache is not None:
            self._cache.save()

        for batch_start in range(0, len(ready), self._batch_size):
            batch = ready[batch_start : batch_start + self._batch_size]
            self._store.upsert_chunks(
                collection,
                [chunk for chunk, _ in batch],
                [vector for _, vector in batch],
            )

        statistics = IndexStatistics(
            total_chunks=repository_chunks.total_chunks,
            embedded_chunks=embedded_count,
            cached_chunks=cached_count,
            failed_chunks=failed_count,
            elapsed_seconds=round(time.perf_counter() - start, 3),
        )
        logger.info(
            "Indexing complete for %s -> %s: %s",
            repository_chunks.repository_name,
            collection,
            statistics,
        )
        return IndexedRepository(
            repository_name=repository_chunks.repository_name,
            collection_name=collection,
            embedding_model=self._provider.model_name,
            vector_dimension=self._provider.dimension,
            statistics=statistics,
        )

    def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Call the provider, retrying with exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return self._provider.embed_batch(texts)
            except Exception as exc:
                last_error = exc
                if attempt + 1 < self._max_retries:
                    delay = self._backoff_seconds * (2**attempt)
                    logger.warning(
                        "Embedding attempt %d/%d failed (%s); retrying in %.1fs",
                        attempt + 1,
                        self._max_retries,
                        exc,
                        delay,
                    )
                    self._sleep(delay)
        assert last_error is not None
        raise last_error


def default_collection_name(repository_name: str) -> str:
    """Sanitized Qdrant collection name for a repository."""
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", repository_name).strip("_").lower()
    return f"codeatlas_{slug or 'repository'}"

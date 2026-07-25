"""Unit tests for the embedding pipeline and Qdrant indexing.

The embedding provider is always mocked — no live API calls. Qdrant runs
in the client's local in-memory mode — no server required.
"""

import hashlib
from pathlib import Path
from typing import ClassVar

from qdrant_client import QdrantClient

from chunking import Chunk, ChunkType, RepositoryChunks
from embeddings import (
    EmbeddingCache,
    EmbeddingProvider,
    IndexBuilder,
    QdrantVectorStore,
    chunk_payload,
    default_collection_name,
    point_id_for,
)
from scanner import FileCategory, ProgrammingLanguage


class FakeProvider(EmbeddingProvider):
    """Deterministic provider that records every batch it receives."""

    model_name: ClassVar[str] = "fake-embedding-001"
    dimension: ClassVar[int] = 8

    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.batches.append(list(texts))
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in digest[: self.dimension]]


class FlakyProvider(FakeProvider):
    """Fails a fixed number of times before succeeding."""

    def __init__(self, failures: int) -> None:
        super().__init__()
        self._failures = failures

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._failures > 0:
            self._failures -= 1
            raise ConnectionError("transient failure")
        return super().embed_batch(texts)


def _chunk(index: int, content: str | None = None) -> Chunk:
    return Chunk(
        chunk_id=f"chunk{index:04d}",
        repository_name="testrepo",
        relative_path=f"src/module{index}.py",
        language=ProgrammingLanguage.PYTHON,
        category=FileCategory.SOURCE_CODE,
        chunk_type=ChunkType.FUNCTION,
        symbol_name=f"func{index}",
        qualified_name=f"func{index}",
        start_line=1,
        end_line=5,
        content=content if content is not None else f"def func{index}():\n    pass",
        token_estimate=10,
        imports=["os"],
        dependencies=["src/other.py"],
    )


def _chunks(count: int) -> RepositoryChunks:
    return RepositoryChunks(
        repository_name="testrepo", chunks=[_chunk(i) for i in range(count)]
    )


def _store() -> QdrantVectorStore:
    return QdrantVectorStore(client=QdrantClient(":memory:"))


class TestBatching:
    def test_requests_are_batched(self) -> None:
        provider = FakeProvider()
        builder = IndexBuilder(provider, _store(), batch_size=2)

        result = builder.build(_chunks(5))

        assert [len(batch) for batch in provider.batches] == [2, 2, 1]
        assert result.statistics.embedded_chunks == 5

    def test_single_batch_when_under_limit(self) -> None:
        provider = FakeProvider()
        builder = IndexBuilder(provider, _store(), batch_size=32)

        builder.build(_chunks(5))

        assert len(provider.batches) == 1


class TestCache:
    def test_second_run_hits_cache(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(tmp_path / "cache.json")
        chunks = _chunks(4)
        store = _store()

        first_provider = FakeProvider()
        first = IndexBuilder(first_provider, store, cache).build(chunks)
        assert first.statistics.embedded_chunks == 4
        assert first.statistics.cached_chunks == 0

        # Fresh cache instance proves persistence to disk.
        reloaded = EmbeddingCache(tmp_path / "cache.json")
        second_provider = FakeProvider()
        second = IndexBuilder(second_provider, store, reloaded).build(chunks)

        assert second.statistics.cached_chunks == 4
        assert second.statistics.embedded_chunks == 0
        assert second_provider.batches == []  # provider never called

    def test_changed_content_misses_cache(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(tmp_path / "cache.json")
        store = _store()
        original = RepositoryChunks(
            repository_name="testrepo", chunks=[_chunk(0, content="old body")]
        )
        IndexBuilder(FakeProvider(), store, cache).build(original)

        changed = RepositoryChunks(
            repository_name="testrepo", chunks=[_chunk(0, content="new body")]
        )
        provider = FakeProvider()
        result = IndexBuilder(provider, store, cache).build(changed)

        assert result.statistics.embedded_chunks == 1
        assert result.statistics.cached_chunks == 0
        assert provider.batches == [["new body"]]

    def test_cache_key_includes_content_hash(self) -> None:
        key_a = EmbeddingCache.key_for(_chunk(0, content="aaa"))
        key_b = EmbeddingCache.key_for(_chunk(0, content="bbb"))
        assert key_a != key_b
        assert key_a.startswith("chunk0000:")


class TestRetries:
    def test_transient_failure_retried_with_backoff(self) -> None:
        provider = FlakyProvider(failures=2)
        delays: list[float] = []
        builder = IndexBuilder(
            provider,
            _store(),
            max_retries=3,
            backoff_seconds=1.0,
            sleep=delays.append,
        )

        result = builder.build(_chunks(2))

        assert result.statistics.embedded_chunks == 2
        assert result.statistics.failed_chunks == 0
        assert delays == [1.0, 2.0]  # exponential backoff

    def test_permanent_failure_counts_failed_chunks(self) -> None:
        provider = FlakyProvider(failures=99)
        delays: list[float] = []
        builder = IndexBuilder(provider, _store(), max_retries=3, sleep=delays.append)

        result = builder.build(_chunks(3))

        assert result.statistics.failed_chunks == 3
        assert result.statistics.embedded_chunks == 0
        assert len(delays) == 2  # retries 1 and 2 slept; attempt 3 gave up

    def test_failed_batch_does_not_abort_other_batches(self) -> None:
        provider = FlakyProvider(failures=3)  # first batch exhausts retries
        builder = IndexBuilder(
            provider, _store(), batch_size=2, max_retries=3, sleep=lambda _: None
        )

        result = builder.build(_chunks(4))

        assert result.statistics.failed_chunks == 2
        assert result.statistics.embedded_chunks == 2


class TestQdrantPayload:
    def test_payload_contains_required_fields(self) -> None:
        payload = chunk_payload(_chunk(7))

        assert payload == {
            "chunk_id": "chunk0007",
            "repository_name": "testrepo",
            "relative_path": "src/module7.py",
            "chunk_type": "function",
            "language": "python",
            "category": "source_code",
            "symbol_name": "func7",
            "qualified_name": "func7",
            "start_line": 1,
            "end_line": 5,
            "imports": ["os"],
            "dependencies": ["src/other.py"],
            "token_estimate": 10,
        }
        assert (
            "content" not in payload
        )  # vector stored separately, content not in payload

    def test_points_written_to_qdrant(self) -> None:
        client = QdrantClient(":memory:")
        store = QdrantVectorStore(client=client)
        builder = IndexBuilder(FakeProvider(), store)

        result = builder.build(_chunks(3))

        assert store.count(result.collection_name) == 3
        point_id = point_id_for("chunk0000")
        [point] = client.retrieve(
            result.collection_name, ids=[point_id], with_payload=True
        )
        assert point.payload["chunk_id"] == "chunk0000"
        assert point.payload["chunk_type"] == "function"

    def test_reindexing_upserts_not_duplicates(self, tmp_path: Path) -> None:
        client = QdrantClient(":memory:")
        store = QdrantVectorStore(client=client)
        chunks = _chunks(3)

        IndexBuilder(FakeProvider(), store).build(chunks)
        IndexBuilder(FakeProvider(), store).build(chunks)

        assert store.count(default_collection_name("testrepo")) == 3

    def test_collection_created_automatically(self) -> None:
        client = QdrantClient(":memory:")
        store = QdrantVectorStore(client=client)

        IndexBuilder(FakeProvider(), store).build(_chunks(1))

        assert client.collection_exists("codeatlas_testrepo")

    def test_point_ids_deterministic(self) -> None:
        assert point_id_for("abc") == point_id_for("abc")
        assert point_id_for("abc") != point_id_for("abd")


class TestIndexStatistics:
    def test_statistics_shape(self, tmp_path: Path) -> None:
        cache = EmbeddingCache(tmp_path / "cache.json")
        store = _store()
        IndexBuilder(FakeProvider(), store, cache).build(_chunks(2))

        # Second run: 2 cached; add a third chunk that gets embedded.
        chunks = RepositoryChunks(
            repository_name="testrepo",
            chunks=[_chunk(0), _chunk(1), _chunk(2)],
        )
        result = IndexBuilder(FakeProvider(), store, cache).build(chunks)

        stats = result.statistics
        assert stats.total_chunks == 3
        assert stats.cached_chunks == 2
        assert stats.embedded_chunks == 1
        assert stats.failed_chunks == 0
        assert stats.elapsed_seconds >= 0.0

    def test_indexed_repository_metadata(self) -> None:
        result = IndexBuilder(FakeProvider(), _store()).build(_chunks(1))

        assert result.repository_name == "testrepo"
        assert result.collection_name == "codeatlas_testrepo"
        assert result.embedding_model == "fake-embedding-001"
        assert result.vector_dimension == 8

    def test_collection_name_sanitized(self) -> None:
        assert default_collection_name("My Repo-2!") == "codeatlas_my_repo_2"

"""Unit tests for the semantic retrieval engine.

Embedding generation is mocked with a dict-based provider whose vectors are
handcrafted, so cosine-similarity ordering is exactly predictable. Qdrant
runs in the client's in-memory mode.
"""

from typing import ClassVar

import pytest
from qdrant_client import QdrantClient

from chunking import Chunk, ChunkType, RepositoryChunks
from embeddings import EmbeddingProvider, IndexBuilder, QdrantVectorStore
from retrieval import RetrievalResult, SemanticRetriever
from scanner import FileCategory, ProgrammingLanguage

COLLECTION = "codeatlas_testrepo"


class MappedProvider(EmbeddingProvider):
    """Returns handcrafted vectors for known texts."""

    model_name: ClassVar[str] = "mapped-fake-001"
    dimension: ClassVar[int] = 2

    def __init__(self, mapping: dict[str, list[float]]) -> None:
        self._mapping = mapping

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._mapping[text] for text in texts]


def _chunk(
    chunk_id: str,
    content: str,
    *,
    path: str = "src/app.py",
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
    chunk_type: ChunkType = ChunkType.FUNCTION,
    symbol: str | None = "func",
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        repository_name="testrepo",
        relative_path=path,
        language=language,
        category=FileCategory.SOURCE_CODE,
        chunk_type=chunk_type,
        symbol_name=symbol,
        qualified_name=symbol,
        start_line=1,
        end_line=10,
        content=content,
        token_estimate=5,
    )


@pytest.fixture
def provider() -> MappedProvider:
    # Vectors chosen so cosine similarity to query [1, 0] is:
    # exact 1.0 > close ~0.89 > far ~0.45 > orthogonal 0.0
    return MappedProvider(
        {
            "exact match": [1.0, 0.0],
            "close match": [0.9, 0.45],
            "far match": [0.45, 0.9],
            "orthogonal": [0.0, 1.0],
            "the query": [1.0, 0.0],
        }
    )


@pytest.fixture
def client() -> QdrantClient:
    return QdrantClient(":memory:")


def _index(provider: MappedProvider, client: QdrantClient, chunks: list[Chunk]) -> None:
    builder = IndexBuilder(provider, QdrantVectorStore(client=client))
    builder.build(
        RepositoryChunks(repository_name="testrepo", chunks=chunks),
        collection_name=COLLECTION,
    )


class TestSuccessfulRetrieval:
    def test_returns_hits_with_metadata(
        self, provider: MappedProvider, client: QdrantClient
    ) -> None:
        _index(provider, client, [_chunk("c1", "exact match", symbol="target")])
        retriever = SemanticRetriever(provider, COLLECTION, client)

        result = retriever.retrieve("the query")

        assert isinstance(result, RetrievalResult)
        assert result.query == "the query"
        assert result.collection_name == COLLECTION
        assert result.total_found == 1
        hit = result.chunks[0]
        assert hit.chunk_id == "c1"
        assert hit.repository_name == "testrepo"
        assert hit.score == pytest.approx(1.0, abs=1e-6)
        assert hit.chunk.symbol_name == "target"
        assert hit.chunk.relative_path == "src/app.py"
        assert hit.chunk.language is ProgrammingLanguage.PYTHON
        assert hit.chunk.chunk_type is ChunkType.FUNCTION

    def test_result_serializes(self, provider, client) -> None:
        _index(provider, client, [_chunk("c1", "exact match")])
        result = SemanticRetriever(provider, COLLECTION, client).retrieve("the query")

        restored = RetrievalResult.model_validate_json(result.model_dump_json())
        assert restored.chunks[0].chunk_id == "c1"


class TestEmptyCollection:
    def test_missing_collection_returns_empty(self, provider, client) -> None:
        retriever = SemanticRetriever(provider, "does_not_exist", client)

        result = retriever.retrieve("the query")

        assert result.is_empty
        assert result.total_found == 0

    def test_empty_collection_returns_empty(self, provider, client) -> None:
        QdrantVectorStore(client=client).ensure_collection(COLLECTION, 2)
        retriever = SemanticRetriever(provider, COLLECTION, client)

        result = retriever.retrieve("the query")

        assert result.is_empty


class TestFiltering:
    @pytest.fixture
    def retriever(self, provider, client) -> SemanticRetriever:
        _index(
            provider,
            client,
            [
                _chunk(
                    "py1",
                    "exact match",
                    path="src/a.py",
                    language=ProgrammingLanguage.PYTHON,
                    chunk_type=ChunkType.FUNCTION,
                ),
                _chunk(
                    "md1",
                    "close match",
                    path="README.md",
                    language=ProgrammingLanguage.MARKDOWN,
                    chunk_type=ChunkType.DOCUMENTATION,
                    symbol=None,
                ),
                _chunk(
                    "py2",
                    "far match",
                    path="src/b.py",
                    language=ProgrammingLanguage.PYTHON,
                    chunk_type=ChunkType.CLASS,
                ),
            ],
        )
        return SemanticRetriever(provider, COLLECTION, client)

    def test_language_filter(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", language=ProgrammingLanguage.MARKDOWN)
        assert [c.chunk_id for c in result.chunks] == ["md1"]

    def test_chunk_type_filter(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", chunk_type=ChunkType.CLASS)
        assert [c.chunk_id for c in result.chunks] == ["py2"]

    def test_relative_path_filter(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", relative_path="src/a.py")
        assert [c.chunk_id for c in result.chunks] == ["py1"]

    def test_combined_filters(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve(
            "the query",
            language=ProgrammingLanguage.PYTHON,
            chunk_type=ChunkType.FUNCTION,
        )
        assert [c.chunk_id for c in result.chunks] == ["py1"]

    def test_string_filter_values_accepted(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve(
            "the query", language="markdown", chunk_type="documentation"
        )
        assert [c.chunk_id for c in result.chunks] == ["md1"]

    def test_no_match_filter_returns_empty(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", language=ProgrammingLanguage.RUST)
        assert result.is_empty


class TestScoreThreshold:
    @pytest.fixture
    def retriever(self, provider, client) -> SemanticRetriever:
        _index(
            provider,
            client,
            [
                _chunk("c1", "exact match"),
                _chunk("c2", "close match"),
                _chunk("c3", "orthogonal"),
            ],
        )
        return SemanticRetriever(provider, COLLECTION, client)

    def test_threshold_cuts_low_scores(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", score_threshold=0.95)
        assert [c.chunk_id for c in result.chunks] == ["c1"]

    def test_moderate_threshold(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", score_threshold=0.5)
        assert [c.chunk_id for c in result.chunks] == ["c1", "c2"]

    def test_no_threshold_returns_all(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query")
        assert result.total_found == 3


class TestTopKOrdering:
    @pytest.fixture
    def retriever(self, provider, client) -> SemanticRetriever:
        _index(
            provider,
            client,
            [
                _chunk("far", "far match"),
                _chunk("exact", "exact match"),
                _chunk("ortho", "orthogonal"),
                _chunk("close", "close match"),
            ],
        )
        return SemanticRetriever(provider, COLLECTION, client)

    def test_ordered_by_similarity_descending(
        self, retriever: SemanticRetriever
    ) -> None:
        result = retriever.retrieve("the query")

        assert [c.chunk_id for c in result.chunks] == [
            "exact",
            "close",
            "far",
            "ortho",
        ]
        scores = [c.score for c in result.chunks]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_limits_results(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query", top_k=2)

        assert [c.chunk_id for c in result.chunks] == ["exact", "close"]
        assert result.top_k == 2

    def test_default_top_k_is_ten(self, retriever: SemanticRetriever) -> None:
        result = retriever.retrieve("the query")
        assert result.top_k == 10

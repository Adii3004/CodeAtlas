"""Unit tests for the LLM context builder."""

from pathlib import Path

import pytest

from chunking import ChunkBuilder, ChunkType, RepositoryChunks
from context import ContextBuilder, LLMContext
from knowledge import RepositoryKnowledge, build_repository_knowledge
from retrieval.models import ChunkPayload, RetrievalResult, RetrievedChunk
from scanner import RepositoryScanner


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _knowledge(root: Path) -> RepositoryKnowledge:
    return build_repository_knowledge(RepositoryScanner().scan(root))


def _chunks(knowledge: RepositoryKnowledge) -> RepositoryChunks:
    return ChunkBuilder().build(knowledge)


def _hit(chunk, score: float) -> RetrievedChunk:
    payload = ChunkPayload(
        chunk_id=chunk.chunk_id,
        repository_name=chunk.repository_name,
        relative_path=chunk.relative_path,
        chunk_type=chunk.chunk_type,
        language=chunk.language,
        category=chunk.category,
        symbol_name=chunk.symbol_name,
        qualified_name=chunk.qualified_name,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        imports=chunk.imports,
        dependencies=chunk.dependencies,
        token_estimate=chunk.token_estimate,
    )
    return RetrievedChunk(
        chunk_id=chunk.chunk_id,
        score=score,
        repository_name=chunk.repository_name,
        chunk=payload,
    )


def _result(hits: list[RetrievedChunk]) -> RetrievalResult:
    return RetrievalResult(
        query="test query", collection_name="c", top_k=10, chunks=hits
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _write(
        tmp_path,
        "service.py",
        "class Service:\n    pass\n\n\ndef run():\n    pass\n",
    )
    _write(tmp_path, "util.py", "def helper():\n    pass\n")
    _write(tmp_path, "README.md", "# Guide\nSome documentation here.\n")
    return tmp_path


def _find(chunks: RepositoryChunks, chunk_type: ChunkType, symbol=None):
    for chunk in chunks.chunks:
        if chunk.chunk_type is chunk_type and (
            symbol is None or chunk.symbol_name == symbol
        ):
            return chunk
    raise AssertionError(f"chunk not found: {chunk_type} {symbol}")


class TestDuplicateRemoval:
    def test_duplicate_hits_included_once(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        func = _find(chunks, ChunkType.FUNCTION, "run")

        result = _result([_hit(func, 0.9), _hit(func, 0.8)])
        context = ContextBuilder().build("q", result, knowledge)

        ids = [c.chunk_id for s in context.sections for c in s.chunks]
        assert ids.count(func.chunk_id) == 1


class TestTokenBudgeting:
    def test_oversized_chunk_skipped_whole(self, tmp_path: Path) -> None:
        body = "".join(f"    attr_{i} = {i}\n" for i in range(50))
        _write(tmp_path, "big.py", f"class Huge:\n{body}")
        _write(tmp_path, "small.py", "def tiny():\n    pass\n")
        knowledge = _knowledge(tmp_path)
        chunks = _chunks(knowledge)
        big = _find(chunks, ChunkType.CLASS, "Huge")
        small = _find(chunks, ChunkType.FUNCTION, "tiny")
        assert big.token_estimate > small.token_estimate * 5

        # Budget: summary + small function fit; the huge class does not.
        summary_tokens = ContextBuilder._repository_summary_chunk(
            knowledge
        ).token_estimate
        budget = summary_tokens + small.token_estimate + 1

        result = _result([_hit(big, 0.95), _hit(small, 0.9)])
        context = ContextBuilder(max_tokens=budget).build("q", result, knowledge)

        included = {c.chunk_id for s in context.sections for c in s.chunks}
        assert small.chunk_id in included
        assert big.chunk_id not in included
        assert context.statistics.skipped_chunks == 1
        assert context.statistics.included_chunks == 2  # summary + small
        assert context.statistics.total_tokens <= budget

    def test_content_never_truncated(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        func = _find(chunks, ChunkType.FUNCTION, "helper")

        context = ContextBuilder().build("q", _result([_hit(func, 0.9)]), knowledge)

        [included] = [
            c for s in context.sections for c in s.chunks if c.chunk_id == func.chunk_id
        ]
        assert included.content == func.content  # byte-identical

    def test_statistics_totals(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        hits = [
            _hit(_find(chunks, ChunkType.FUNCTION, "run"), 0.9),
            _hit(_find(chunks, ChunkType.FUNCTION, "helper"), 0.8),
        ]

        context = ContextBuilder().build("q", _result(hits), knowledge)

        stats = context.statistics
        assert stats.included_chunks == context.total_chunks
        assert stats.total_tokens == context.estimated_tokens
        assert stats.total_tokens == sum(
            c.token_estimate for s in context.sections for c in s.chunks
        )


class TestOrdering:
    def test_higher_score_first_within_section(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        low = _hit(_find(chunks, ChunkType.FUNCTION, "run"), 0.3)
        high = _hit(_find(chunks, ChunkType.FUNCTION, "helper"), 0.9)

        context = ContextBuilder().build("q", _result([low, high]), knowledge)

        [functions] = [s for s in context.sections if s.title == "Relevant Functions"]
        assert [c.symbol_name for c in functions.chunks] == ["helper", "run"]

    def test_documentation_after_code(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        doc = _find(chunks, ChunkType.DOCUMENTATION)
        func = _find(chunks, ChunkType.FUNCTION, "run")

        # Documentation scored higher, but still ordered after code sections.
        context = ContextBuilder().build(
            "q", _result([_hit(doc, 0.99), _hit(func, 0.5)]), knowledge
        )

        titles = [s.title for s in context.sections]
        assert titles.index("Relevant Functions") < titles.index("Documentation")
        priorities = [s.priority for s in context.sections]
        assert priorities == sorted(priorities)


class TestSectionGrouping:
    def test_chunk_types_map_to_sections(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        hits = [
            _hit(_find(chunks, ChunkType.FILE_SUMMARY), 0.9),
            _hit(_find(chunks, ChunkType.CLASS, "Service"), 0.8),
            _hit(_find(chunks, ChunkType.FUNCTION, "run"), 0.7),
            _hit(_find(chunks, ChunkType.DOCUMENTATION), 0.6),
        ]

        context = ContextBuilder().build("q", _result(hits), knowledge)

        by_title = {s.title: s for s in context.sections}
        assert "Repository Summary" in by_title
        assert by_title["Relevant Classes"].chunks[0].symbol_name == "Service"
        assert by_title["Relevant Functions"].chunks[0].symbol_name == "run"
        assert by_title["Documentation"].chunks[0].chunk_type is (
            ChunkType.DOCUMENTATION
        )

    def test_contiguous_same_file_chunks_merged(self, tmp_path: Path) -> None:
        # Two functions with adjacent line ranges in one file.
        _write(
            tmp_path,
            "pair.py",
            "def first():\n    pass\ndef second():\n    pass\n",
        )
        knowledge = _knowledge(tmp_path)
        chunks = _chunks(knowledge)
        first = _find(chunks, ChunkType.FUNCTION, "first")
        second = _find(chunks, ChunkType.FUNCTION, "second")
        assert second.start_line == first.end_line + 1  # truly contiguous

        context = ContextBuilder().build(
            "q", _result([_hit(first, 0.9), _hit(second, 0.8)]), knowledge
        )

        [functions] = [s for s in context.sections if s.title == "Relevant Functions"]
        [merged] = functions.chunks
        assert "def first" in merged.content
        assert "def second" in merged.content
        assert merged.start_line == first.start_line
        assert merged.end_line == second.end_line
        assert merged.score == 0.9  # best score kept

    def test_non_contiguous_chunks_not_merged(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        cls = _find(chunks, ChunkType.CLASS, "Service")  # lines 1-2
        func = _find(chunks, ChunkType.FUNCTION, "run")  # lines 5-6 (gap)

        context = ContextBuilder().build(
            "q", _result([_hit(cls, 0.9), _hit(func, 0.8)]), knowledge
        )

        all_ids = [c.chunk_id for s in context.sections for c in s.chunks]
        assert cls.chunk_id in all_ids
        assert func.chunk_id in all_ids


class TestEmptyRetrieval:
    def test_empty_retrieval_still_has_summary(self, repo: Path) -> None:
        knowledge = _knowledge(repo)

        context = ContextBuilder().build("q", _result([]), knowledge)

        assert isinstance(context, LLMContext)
        [summary] = context.sections
        assert summary.title == "Repository Summary"
        assert context.total_chunks == 1
        assert context.statistics.skipped_chunks == 0
        assert knowledge.repository_name in summary.chunks[0].content

    def test_to_text_renders(self, repo: Path) -> None:
        knowledge = _knowledge(repo)
        chunks = _chunks(knowledge)
        func = _find(chunks, ChunkType.FUNCTION, "run")

        context = ContextBuilder().build(
            "where is run?", _result([_hit(func, 0.9)]), knowledge
        )
        text = context.to_text()

        assert "Query: where is run?" in text
        assert "=== Relevant Functions ===" in text
        assert "service.py :: run" in text
        assert "def run" in text

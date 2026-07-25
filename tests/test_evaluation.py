"""Unit tests for the RAG evaluation framework. All inputs are mocked."""

from datetime import datetime

import pytest

from ai.models import AIResponse
from chunking import ChunkType
from context.models import (
    ContextChunk,
    ContextSection,
    ContextStatistics,
    LLMContext,
)
from evaluation import AnswerEvaluator, EvaluationResult
from retrieval.models import ChunkPayload, RetrievalResult, RetrievedChunk
from scanner import FileCategory, ProgrammingLanguage


def _payload(chunk_id: str, path: str) -> ChunkPayload:
    return ChunkPayload(
        chunk_id=chunk_id,
        repository_name="testrepo",
        relative_path=path,
        chunk_type=ChunkType.FUNCTION,
        language=ProgrammingLanguage.PYTHON,
        category=FileCategory.SOURCE_CODE,
        start_line=1,
        end_line=5,
        token_estimate=10,
    )


def _retrieval(hits: list[tuple[str, str, float]]) -> RetrievalResult:
    return RetrievalResult(
        query="q",
        collection_name="c",
        top_k=10,
        chunks=[
            RetrievedChunk(
                chunk_id=cid,
                score=score,
                repository_name="testrepo",
                chunk=_payload(cid, path),
            )
            for cid, path, score in hits
        ],
    )


def _context_chunk(path: str, score: float, tokens: int = 100) -> ContextChunk:
    return ContextChunk(
        chunk_id=f"id-{path}",
        relative_path=path,
        chunk_type=ChunkType.FUNCTION,
        symbol_name="f",
        start_line=1,
        end_line=5,
        score=score,
        token_estimate=tokens,
        content="def f():\n    pass",
    )


def _context(chunks: list[ContextChunk], skipped: int = 0) -> LLMContext:
    tokens = sum(c.token_estimate for c in chunks)
    sections = (
        [ContextSection(title="Relevant Functions", priority=4, chunks=chunks)]
        if chunks
        else []
    )
    return LLMContext(
        original_query="q",
        repository_name="testrepo",
        generated_at=datetime(2026, 7, 25),
        total_chunks=len(chunks),
        estimated_tokens=tokens,
        sections=sections,
        statistics=ContextStatistics(
            included_chunks=len(chunks),
            skipped_chunks=skipped,
            total_tokens=tokens,
        ),
    )


def _response(answer: str, referenced: list[str]) -> AIResponse:
    return AIResponse(
        answer=answer,
        model="fake",
        prompt_tokens_estimate=100,
        completion_tokens_estimate=50,
        total_tokens_estimate=150,
        referenced_files=referenced,
        generation_time=0.5,
    )


class TestPerfectAnswer:
    def test_high_confidence_no_warnings(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.95), ("c2", "src/b.py", 0.9)])
        context = _context(
            [
                _context_chunk("src/a.py", 0.95, 1200),
                _context_chunk("src/b.py", 0.9, 1000),
            ]
        )
        response = _response(
            "The logic is in src/a.py, helped by src/b.py.",
            ["src/a.py", "src/b.py"],
        )

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        # retrieval ~0.925*30=27.75 | context 25 (2200>=2000)
        # grounding 2/2*25=25 | hallucination 20 -> ~98
        assert result.confidence >= 95
        assert result.warnings == []
        assert not result.hallucination.has_hallucinations
        assert result.grounding.referenced_files_ratio == 1.0
        assert result.grounding.coverage_ratio == 1.0
        assert result.retrieval.retrieved_chunks == 2
        assert result.retrieval.context_tokens == 2200

    def test_result_serializes(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.9)])
        context = _context([_context_chunk("src/a.py", 0.9)])
        response = _response("See src/a.py.", ["src/a.py"])

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)
        restored = EvaluationResult.model_validate_json(result.model_dump_json())
        assert restored.confidence == result.confidence


class TestHallucinatedAnswer:
    def test_unknown_path_detected(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.9)])
        context = _context([_context_chunk("src/a.py", 0.9, 2000)])
        response = _response(
            "Implemented in src/a.py and configured by magic/settings_loader.py.",
            ["src/a.py"],
        )

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        assert result.hallucination.suspected_paths == ["magic/settings_loader.py"]
        assert any("hallucinations" in w for w in result.warnings)

    def test_hallucination_lowers_confidence(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.9)])
        context = _context([_context_chunk("src/a.py", 0.9, 2000)])
        clean = _response("See src/a.py.", ["src/a.py"])
        dirty = _response("See src/a.py and also ghost/phantom.py.", ["src/a.py"])

        evaluator = AnswerEvaluator()
        clean_score = evaluator.evaluate("q", retrieval, context, clean)
        dirty_score = evaluator.evaluate("q", retrieval, context, dirty)

        assert dirty_score.confidence == clean_score.confidence - 10

    def test_known_files_are_not_hallucinations(self) -> None:
        retrieval = _retrieval([("c1", "src/deep/a.py", 0.9)])
        context = _context([_context_chunk("src/deep/a.py", 0.9)])
        # Bare filename, full path, and path suffix must all be accepted.
        response = _response(
            "See a.py, also called src/deep/a.py or deep/a.py.",
            ["src/deep/a.py"],
        )

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        assert result.hallucination.suspected_paths == []


class TestEmptyRetrieval:
    def test_empty_retrieval_warnings_and_low_confidence(self) -> None:
        retrieval = _retrieval([])
        context = _context([])
        response = _response("I cannot find this in the context.", [])

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        assert "No chunks were retrieved for this query." in result.warnings
        assert any(w.startswith("Insufficient context") for w in result.warnings)
        # Only the hallucination component (20) can score.
        assert result.confidence <= 20
        assert result.retrieval.retrieved_chunks == 0
        assert result.grounding.major_files == []


class TestLowConfidenceAnswer:
    def test_weak_retrieval_small_context_no_references(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.15)])
        context = _context([_context_chunk("src/a.py", 0.15, 100)])
        response = _response("Possibly somewhere in the code.", [])

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        # retrieval 0.15*30=4.5 | context 100/2000*25=1.25 | grounding 0
        # hallucination 20 -> ~26
        assert result.confidence <= 30
        assert "Answer references no files from the context." in result.warnings

    def test_partial_coverage(self) -> None:
        retrieval = _retrieval(
            [("c1", "src/a.py", 0.9), ("c2", "src/b.py", 0.8), ("c3", "src/c.py", 0.7)]
        )
        context = _context(
            [
                _context_chunk("src/a.py", 0.9),
                _context_chunk("src/b.py", 0.8),
                _context_chunk("src/c.py", 0.7),
            ]
        )
        response = _response("Mostly in src/a.py.", ["src/a.py"])

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        assert result.grounding.major_files == ["src/a.py", "src/b.py", "src/c.py"]
        assert result.grounding.covered_major_files == ["src/a.py"]
        assert result.grounding.coverage_ratio == pytest.approx(1 / 3, abs=1e-3)


class TestDiagnostics:
    def test_token_budget_warning(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.9)])
        context = _context([_context_chunk("src/a.py", 0.9, 2000)], skipped=4)
        response = _response("See src/a.py.", ["src/a.py"])

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        assert any(w.startswith("Token budget exceeded: 4") for w in result.warnings)

    def test_insufficient_context_threshold_configurable(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.9)])
        context = _context([_context_chunk("src/a.py", 0.9, 600)])
        response = _response("See src/a.py.", ["src/a.py"])

        default = AnswerEvaluator().evaluate("q", retrieval, context, response)
        strict = AnswerEvaluator(min_context_tokens=1000).evaluate(
            "q", retrieval, context, response
        )

        assert not any(w.startswith("Insufficient") for w in default.warnings)
        assert any(w.startswith("Insufficient") for w in strict.warnings)

    def test_evaluation_time_recorded(self) -> None:
        retrieval = _retrieval([("c1", "src/a.py", 0.9)])
        context = _context([_context_chunk("src/a.py", 0.9)])
        response = _response("See src/a.py.", ["src/a.py"])

        result = AnswerEvaluator().evaluate("q", retrieval, context, response)

        assert result.evaluation_time >= 0.0

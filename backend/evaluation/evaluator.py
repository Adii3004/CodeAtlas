"""AnswerEvaluator: deterministic quality metrics for one RAG answer.

Confidence score (0-100), computed as the sum of four components:

1. Retrieval score (0-30): mean similarity score of the top 3 retrieval
   hits, clamped to [0, 1], times 30. Zero when nothing was retrieved.
2. Context size (0-25): ``min(context_tokens / sufficient_tokens, 1) * 25``
   (default ``sufficient_tokens`` = 2000).
3. Referenced files (0-25): ``referenced_files_ratio * 25``, where the
   ratio is referenced files over distinct context files.
4. Hallucination (0-20): starts at 20; each suspected hallucinated path
   subtracts 10 (floor 0).

The total is rounded and clamped to [0, 100]. No LLM is involved.
"""

import logging
import re
import time

from ai.models import AIResponse
from context.models import LLMContext
from evaluation.models import (
    EvaluationResult,
    GroundingStatistics,
    HallucinationCheck,
    RetrievalStatistics,
)
from retrieval.models import RetrievalResult

logger = logging.getLogger(__name__)

#: Path-like tokens in answer text, e.g. `src/app.py` or `README.md`.
_PATH_RE = re.compile(r"[\w][\w./\\-]*\.[A-Za-z]{1,10}\b")

#: Mentions with these extensions are treated as file references.
_FILE_EXTENSIONS = (
    ".py",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".html",
    ".css",
    ".cfg",
    ".ini",
    ".xml",
    ".sh",
)

DEFAULT_MIN_CONTEXT_TOKENS = 500
DEFAULT_SUFFICIENT_TOKENS = 2000
DEFAULT_MAJOR_FILES_LIMIT = 3


class AnswerEvaluator:
    """Evaluates one answer against its retrieval and context artifacts."""

    def __init__(
        self,
        *,
        min_context_tokens: int = DEFAULT_MIN_CONTEXT_TOKENS,
        sufficient_tokens: int = DEFAULT_SUFFICIENT_TOKENS,
        major_files_limit: int = DEFAULT_MAJOR_FILES_LIMIT,
    ) -> None:
        self._min_context_tokens = min_context_tokens
        self._sufficient_tokens = sufficient_tokens
        self._major_files_limit = major_files_limit

    def evaluate(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        context: LLMContext,
        response: AIResponse,
    ) -> EvaluationResult:
        """Evaluate one answer against its retrieval and context."""
        start = time.perf_counter()

        retrieval_stats = RetrievalStatistics(
            retrieved_chunks=retrieval_result.total_found,
            context_chunks=context.statistics.included_chunks,
            context_tokens=context.statistics.total_tokens,
        )
        context_files = self._context_files(context)
        grounding = self._grounding(context, context_files, response)
        hallucination = self._hallucination_check(response, context_files)
        confidence = self._confidence(
            retrieval_result, retrieval_stats, grounding, hallucination
        )
        warnings = self._diagnostics(retrieval_stats, context, grounding, hallucination)

        result = EvaluationResult(
            query=query,
            confidence=confidence,
            warnings=warnings,
            retrieval=retrieval_stats,
            grounding=grounding,
            hallucination=hallucination,
            evaluation_time=round(time.perf_counter() - start, 4),
        )
        logger.info(
            "Evaluation for %r: confidence=%d, %d warning(s)",
            query,
            confidence,
            len(warnings),
        )
        return result

    # ------------------------------------------------------------------ parts

    @staticmethod
    def _context_files(context: LLMContext) -> list[str]:
        """Distinct real file paths in the context (repo summary excluded)."""
        seen: list[str] = []
        for section in context.sections:
            for chunk in section.chunks:
                if chunk.relative_path != "." and chunk.relative_path not in seen:
                    seen.append(chunk.relative_path)
        return seen

    def _grounding(
        self,
        context: LLMContext,
        context_files: list[str],
        response: AIResponse,
    ) -> GroundingStatistics:
        referenced = set(response.referenced_files)
        ratio = min(len(referenced) / len(context_files), 1.0) if context_files else 0.0

        # Major files: the files of the highest-scoring context chunks.
        scored: dict[str, float] = {}
        for section in context.sections:
            for chunk in section.chunks:
                if chunk.relative_path == ".":
                    continue
                scored[chunk.relative_path] = max(
                    scored.get(chunk.relative_path, 0.0), chunk.score
                )
        major = [
            path
            for path, _ in sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))[
                : self._major_files_limit
            ]
        ]
        covered = [path for path in major if path in referenced]
        return GroundingStatistics(
            referenced_files_count=len(referenced),
            referenced_files_ratio=round(ratio, 3),
            major_files=major,
            covered_major_files=covered,
            coverage_ratio=round(len(covered) / len(major), 3) if major else 0.0,
        )

    def _hallucination_check(
        self, response: AIResponse, context_files: list[str]
    ) -> HallucinationCheck:
        """Find file-path mentions that do not exist in the context."""
        known_paths = set(context_files)
        known_names = {path.rsplit("/", 1)[-1] for path in context_files}

        suspected: list[str] = []
        for raw in _PATH_RE.findall(response.answer):
            mention = raw.replace("\\", "/").strip("./")
            if not mention.lower().endswith(_FILE_EXTENSIONS):
                continue
            name = mention.rsplit("/", 1)[-1]
            if mention in known_paths or name in known_names:
                continue
            if any(path.endswith("/" + mention) for path in known_paths):
                continue
            if mention not in suspected:
                suspected.append(mention)
        return HallucinationCheck(suspected_paths=suspected)

    def _confidence(
        self,
        retrieval_result: RetrievalResult,
        retrieval_stats: RetrievalStatistics,
        grounding: GroundingStatistics,
        hallucination: HallucinationCheck,
    ) -> int:
        """Combine the four components documented in the module docstring."""
        top_scores = [hit.score for hit in retrieval_result.chunks[:3]]
        retrieval_component = (
            min(max(sum(top_scores) / len(top_scores), 0.0), 1.0) * 30
            if top_scores
            else 0.0
        )
        context_component = (
            min(retrieval_stats.context_tokens / self._sufficient_tokens, 1.0) * 25
        )
        grounding_component = grounding.referenced_files_ratio * 25
        hallucination_component = max(20 - 10 * len(hallucination.suspected_paths), 0)
        total = (
            retrieval_component
            + context_component
            + grounding_component
            + hallucination_component
        )
        return max(0, min(100, round(total)))

    def _diagnostics(
        self,
        retrieval_stats: RetrievalStatistics,
        context: LLMContext,
        grounding: GroundingStatistics,
        hallucination: HallucinationCheck,
    ) -> list[str]:
        warnings: list[str] = []
        if retrieval_stats.retrieved_chunks == 0:
            warnings.append("No chunks were retrieved for this query.")
        if retrieval_stats.context_tokens < self._min_context_tokens:
            warnings.append(
                f"Insufficient context: only {retrieval_stats.context_tokens} "
                f"tokens (minimum {self._min_context_tokens})."
            )
        if hallucination.has_hallucinations:
            warnings.append(
                "Answer contains possible hallucinations: "
                + ", ".join(hallucination.suspected_paths)
            )
        if context.statistics.skipped_chunks > 0:
            warnings.append(
                f"Token budget exceeded: {context.statistics.skipped_chunks} "
                f"chunk(s) were skipped during context construction."
            )
        if (
            retrieval_stats.retrieved_chunks > 0
            and grounding.referenced_files_count == 0
        ):
            warnings.append("Answer references no files from the context.")
        return warnings

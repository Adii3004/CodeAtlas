"""ContextBuilder: turns retrieval hits into an ordered, budgeted LLMContext.

Content recovery: Qdrant payloads do not store chunk content, so the builder
re-runs the deterministic ChunkBuilder over RepositoryKnowledge and joins
retrieval hits to full chunks by chunk_id.

Ordering: sections by fixed priority (repository summary, files, classes,
functions, documentation, additional) — documentation after code — and
chunks inside each section by similarity score, best first. Duplicate hits
are dropped; contiguous chunks from the same file are merged.

Budgeting: chunks that do not fit the remaining token budget are skipped
whole — content is never truncated.
"""

import logging
from datetime import datetime

from chunking.builder import ChunkBuilder
from chunking.models import Chunk, ChunkType, estimate_tokens
from context.models import (
    ContextChunk,
    ContextSection,
    ContextStatistics,
    LLMContext,
)
from knowledge.models import RepositoryKnowledge
from retrieval.models import RetrievalResult

logger = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 8000

REPOSITORY_SUMMARY_ID = "repository_summary"

_SECTIONS: list[tuple[str, int]] = [
    ("Repository Summary", 1),
    ("Relevant Files", 2),
    ("Relevant Classes", 3),
    ("Relevant Functions", 4),
    ("Documentation", 5),
    ("Additional Context", 6),
]

_SECTION_FOR_CHUNK_TYPE: dict[ChunkType, str] = {
    ChunkType.FILE_SUMMARY: "Relevant Files",
    ChunkType.CLASS: "Relevant Classes",
    ChunkType.FUNCTION: "Relevant Functions",
    ChunkType.DOCUMENTATION: "Documentation",
    ChunkType.MODULE: "Additional Context",
}


class ContextBuilder:
    """Builds an LLMContext from a query, retrieval result, and knowledge."""

    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self._max_tokens = max_tokens

    def build(
        self,
        query: str,
        retrieval_result: RetrievalResult,
        knowledge: RepositoryKnowledge,
        *,
        max_tokens: int | None = None,
    ) -> LLMContext:
        """Build an ordered, token-budgeted LLMContext."""
        budget = max_tokens if max_tokens is not None else self._max_tokens
        chunks_by_id = {
            chunk.chunk_id: chunk for chunk in ChunkBuilder().build(knowledge).chunks
        }

        candidates = self._collect_candidates(retrieval_result, chunks_by_id)
        grouped = self._group_into_sections(candidates)
        summary_chunk = self._repository_summary_chunk(knowledge)
        grouped["Repository Summary"] = [summary_chunk]

        sections: list[ContextSection] = []
        included = 0
        skipped = 0
        total_tokens = 0
        for title, priority in _SECTIONS:
            selected: list[ContextChunk] = []
            for chunk in grouped.get(title, []):
                if total_tokens + chunk.token_estimate > budget:
                    skipped += 1
                    logger.debug(
                        "Skipping %s (%d tokens over budget)",
                        chunk.chunk_id,
                        chunk.token_estimate,
                    )
                    continue
                selected.append(chunk)
                total_tokens += chunk.token_estimate
                included += 1
            if selected:
                sections.append(
                    ContextSection(title=title, priority=priority, chunks=selected)
                )

        context = LLMContext(
            original_query=query,
            repository_name=knowledge.repository_name,
            generated_at=datetime.now(),
            total_chunks=included,
            estimated_tokens=total_tokens,
            sections=sections,
            statistics=ContextStatistics(
                included_chunks=included,
                skipped_chunks=skipped,
                total_tokens=total_tokens,
            ),
        )
        logger.info(
            "Context built for %r: %d chunks, %d tokens (budget %d), %d skipped",
            query,
            included,
            total_tokens,
            budget,
            skipped,
        )
        return context

    def _collect_candidates(
        self,
        retrieval_result: RetrievalResult,
        chunks_by_id: dict[str, Chunk],
    ) -> list[ContextChunk]:
        """Join hits to full chunks, deduplicate, and sort by score."""
        seen: set[str] = set()
        candidates: list[ContextChunk] = []
        for hit in sorted(retrieval_result.chunks, key=lambda h: -h.score):
            if hit.chunk_id in seen:
                continue
            seen.add(hit.chunk_id)
            chunk = chunks_by_id.get(hit.chunk_id)
            if chunk is None:
                logger.warning(
                    "Retrieved chunk %s not found in current repository "
                    "knowledge (stale index?); dropping",
                    hit.chunk_id,
                )
                continue
            candidates.append(
                ContextChunk(
                    chunk_id=chunk.chunk_id,
                    relative_path=chunk.relative_path,
                    chunk_type=chunk.chunk_type,
                    symbol_name=chunk.symbol_name,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    score=hit.score,
                    token_estimate=chunk.token_estimate,
                    content=chunk.content,
                )
            )
        return candidates

    def _group_into_sections(
        self, candidates: list[ContextChunk]
    ) -> dict[str, list[ContextChunk]]:
        """Group score-ordered candidates by section and merge within files."""
        grouped: dict[str, list[ContextChunk]] = {}
        for chunk in candidates:
            section = _SECTION_FOR_CHUNK_TYPE[chunk.chunk_type]
            grouped.setdefault(section, []).append(chunk)
        return {title: _merge_contiguous(chunks) for title, chunks in grouped.items()}

    @staticmethod
    def _repository_summary_chunk(
        knowledge: RepositoryKnowledge,
    ) -> ContextChunk:
        """Synthesize a deterministic repository overview chunk."""
        top_languages = ", ".join(
            f"{language.value} ({count})"
            for language, count in list(knowledge.inventory.language_counts.items())[:5]
        )
        content = "\n".join(
            [
                f"Repository: {knowledge.repository_name}",
                f"Total files: {knowledge.total_files} "
                f"({len(knowledge.parsed_files)} parsed)",
                f"Top languages: {top_languages or '(none)'}",
                f"Total symbols: {knowledge.total_symbols} | "
                f"Total imports: {knowledge.total_imports}",
            ]
        )
        return ContextChunk(
            chunk_id=REPOSITORY_SUMMARY_ID,
            relative_path=".",
            chunk_type=ChunkType.FILE_SUMMARY,
            symbol_name=None,
            start_line=1,
            end_line=1,
            score=1.0,
            token_estimate=estimate_tokens(content),
            content=content,
        )


def _merge_contiguous(chunks: list[ContextChunk]) -> list[ContextChunk]:
    """Merge same-file chunks whose line ranges touch or overlap.

    Input is score-ordered; merging keeps the best (first) chunk's score and
    id, joins contents in line order, and sums token estimates. Non-mergeable
    chunks keep their score order.
    """
    by_file: dict[str, list[ContextChunk]] = {}
    order: list[str] = []
    for chunk in chunks:
        if chunk.relative_path not in by_file:
            order.append(chunk.relative_path)
        by_file.setdefault(chunk.relative_path, []).append(chunk)

    merged_by_id: dict[str, ContextChunk] = {}
    replaced: dict[str, str] = {}
    for path in order:
        file_chunks = sorted(by_file[path], key=lambda c: c.start_line)
        current = file_chunks[0]
        for nxt in file_chunks[1:]:
            if nxt.start_line <= current.end_line + 1:
                best, other = (
                    (current, nxt) if current.score >= nxt.score else (nxt, current)
                )
                current = ContextChunk(
                    chunk_id=best.chunk_id,
                    relative_path=path,
                    chunk_type=best.chunk_type,
                    symbol_name=best.symbol_name,
                    start_line=min(current.start_line, nxt.start_line),
                    end_line=max(current.end_line, nxt.end_line),
                    score=best.score,
                    token_estimate=current.token_estimate + nxt.token_estimate,
                    content=current.content + "\n" + nxt.content,
                )
                replaced[other.chunk_id] = best.chunk_id
            else:
                merged_by_id[current.chunk_id] = current
                current = nxt
        merged_by_id[current.chunk_id] = current

    result: list[ContextChunk] = []
    emitted: set[str] = set()
    for chunk in chunks:  # original score order
        final_id = chunk.chunk_id
        while final_id in replaced:
            final_id = replaced[final_id]
        if final_id in emitted or final_id not in merged_by_id:
            continue
        emitted.add(final_id)
        result.append(merged_by_id[final_id])
    return result

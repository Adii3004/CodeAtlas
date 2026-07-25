"""Strongly typed models for LLM context construction."""

from datetime import datetime

from pydantic import BaseModel

from chunking.models import ChunkType


class ContextChunk(BaseModel):
    """One piece of content selected for the LLM context."""

    chunk_id: str
    relative_path: str
    chunk_type: ChunkType
    symbol_name: str | None = None
    start_line: int
    end_line: int
    score: float
    token_estimate: int
    content: str


class ContextSection(BaseModel):
    """A titled, prioritized group of context chunks.

    Lower priority numbers appear earlier in the context.
    """

    title: str
    priority: int
    chunks: list[ContextChunk]


class ContextStatistics(BaseModel):
    """Budgeting outcome for one context build."""

    included_chunks: int
    skipped_chunks: int
    total_tokens: int


class LLMContext(BaseModel):
    """Everything needed to ground an LLM answer, ordered and budgeted."""

    original_query: str
    repository_name: str
    generated_at: datetime
    total_chunks: int
    estimated_tokens: int
    sections: list[ContextSection]
    statistics: ContextStatistics

    def to_text(self) -> str:
        """Render the context as plain text (no LLM involved)."""
        lines: list[str] = [
            f"Query: {self.original_query}",
            f"Repository: {self.repository_name}",
            "",
        ]
        for section in self.sections:
            lines.append(f"=== {section.title} ===")
            for chunk in section.chunks:
                location = chunk.relative_path
                if chunk.symbol_name:
                    location += f" :: {chunk.symbol_name}"
                lines.append(
                    f"--- {location} (lines {chunk.start_line}-{chunk.end_line}) ---"
                )
                lines.append(chunk.content)
                lines.append("")
        return "\n".join(lines)

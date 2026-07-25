"""Chunk models: strongly typed units of repository content."""

from enum import StrEnum

from pydantic import BaseModel, Field

from scanner.classifier import FileCategory
from scanner.language import ProgrammingLanguage

#: Approximate characters per token used by the deterministic estimator.
CHARS_PER_TOKEN = 4


class ChunkType(StrEnum):
    """What kind of content a chunk carries."""

    FILE_SUMMARY = "file_summary"
    CLASS = "class"
    FUNCTION = "function"
    MODULE = "module"
    DOCUMENTATION = "documentation"


class Chunk(BaseModel):
    """One embeddable unit of repository content."""

    chunk_id: str
    repository_name: str
    relative_path: str
    language: ProgrammingLanguage
    category: FileCategory
    chunk_type: ChunkType
    symbol_name: str | None = None
    qualified_name: str | None = None
    start_line: int
    end_line: int
    content: str
    token_estimate: int
    imports: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


class RepositoryChunks(BaseModel):
    """All chunks produced for one repository."""

    repository_name: str
    chunks: list[Chunk]

    @property
    def total_chunks(self) -> int:
        """Number of chunks produced for the repository."""
        return len(self.chunks)

    def get_by_type(self, chunk_type: ChunkType) -> list[Chunk]:
        """All chunks of one type, in original order."""
        return [chunk for chunk in self.chunks if chunk.chunk_type is chunk_type]

    def get_chunks_for_file(self, relative_path: str) -> list[Chunk]:
        """All chunks produced from one file."""
        return [chunk for chunk in self.chunks if chunk.relative_path == relative_path]


def estimate_tokens(content: str) -> int:
    """Deterministic token estimate: ~4 characters per token, minimum 1
    for non-empty content."""
    if not content:
        return 0
    return max(1, round(len(content) / CHARS_PER_TOKEN))

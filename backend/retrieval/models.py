"""Result models for semantic retrieval."""

from pydantic import BaseModel, Field

from chunking.models import ChunkType
from scanner.classifier import FileCategory
from scanner.language import ProgrammingLanguage


class ChunkPayload(BaseModel):
    """Chunk metadata as stored in the Qdrant payload.

    Mirrors the payload written by the indexing step; chunk content is not
    stored in Qdrant and therefore is not part of retrieval results.
    """

    chunk_id: str
    repository_name: str
    relative_path: str
    chunk_type: ChunkType
    language: ProgrammingLanguage
    category: FileCategory
    symbol_name: str | None = None
    qualified_name: str | None = None
    start_line: int
    end_line: int
    imports: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    token_estimate: int


class RetrievedChunk(BaseModel):
    """One search hit."""

    chunk_id: str
    score: float
    repository_name: str
    chunk: ChunkPayload


class RetrievalResult(BaseModel):
    """Outcome of one semantic query."""

    query: str
    collection_name: str
    top_k: int
    chunks: list[RetrievedChunk]

    @property
    def total_found(self) -> int:
        """Number of retrieved chunks."""
        return len(self.chunks)

    @property
    def is_empty(self) -> bool:
        """True when nothing was retrieved."""
        return not self.chunks

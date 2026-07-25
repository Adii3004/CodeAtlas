"""Models for RAG answer evaluation."""

from pydantic import BaseModel, Field


class RetrievalStatistics(BaseModel):
    """How much material the pipeline gathered."""

    retrieved_chunks: int
    context_chunks: int
    context_tokens: int


class GroundingStatistics(BaseModel):
    """How well the answer is anchored in the supplied context."""

    referenced_files_count: int
    referenced_files_ratio: float
    major_files: list[str] = Field(default_factory=list)
    covered_major_files: list[str] = Field(default_factory=list)
    coverage_ratio: float


class HallucinationCheck(BaseModel):
    """File-path mentions in the answer that are not part of the context."""

    suspected_paths: list[str] = Field(default_factory=list)

    @property
    def has_hallucinations(self) -> bool:
        """True when any suspected path was found."""
        return bool(self.suspected_paths)


class EvaluationResult(BaseModel):
    """Complete heuristic evaluation of one generated answer."""

    query: str
    confidence: int  # 0-100
    warnings: list[str] = Field(default_factory=list)
    retrieval: RetrievalStatistics
    grounding: GroundingStatistics
    hallucination: HallucinationCheck
    evaluation_time: float

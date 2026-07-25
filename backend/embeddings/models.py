"""Result models for the indexing pipeline."""

from pydantic import BaseModel


class IndexStatistics(BaseModel):
    """Outcome counters for one indexing run."""

    total_chunks: int
    embedded_chunks: int
    cached_chunks: int
    failed_chunks: int
    elapsed_seconds: float


class IndexedRepository(BaseModel):
    """One repository successfully indexed into Qdrant."""

    repository_name: str
    collection_name: str
    embedding_model: str
    vector_dimension: int
    statistics: IndexStatistics

"""Response model for AI answer generation."""

from pydantic import BaseModel, Field


class AIResponse(BaseModel):
    """One grounded answer to one query."""

    answer: str
    model: str
    prompt_tokens_estimate: int
    completion_tokens_estimate: int
    total_tokens_estimate: int
    referenced_files: list[str] = Field(default_factory=list)
    generation_time: float

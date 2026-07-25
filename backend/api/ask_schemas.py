"""Request/response models for the question answering endpoint."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    collection_name: str = Field(min_length=1)
    repository_path: str = Field(min_length=1)
    question: str = Field(min_length=1)
    top_k: int = Field(default=10, ge=1, le=50)
    max_context_tokens: int = Field(default=4000, ge=100, le=100_000)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "collection_name": "codeatlas_my_repo",
                    "repository_path": "C:/projects/my-repo",
                    "question": "How does authentication work?",
                    "top_k": 10,
                    "max_context_tokens": 4000,
                    "temperature": 0.2,
                }
            ]
        }
    }


class AskResponse(BaseModel):
    answer: str
    confidence: int
    referenced_files: list[str]
    retrieved_chunks: int
    context_tokens: int
    warnings: list[str]
    generation_time: float

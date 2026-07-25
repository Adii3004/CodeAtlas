"""Question answering endpoint. The route only calls the AIService."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.ask_schemas import AskRequest, AskResponse
from api.dependencies import get_ai_service
from api.envelope import ApiResponse, error_example
from scanner.repository_scanner import ScanError
from services.ai_service import AIService, AnswerGenerationError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI"])


@router.post(
    "/ask",
    response_model=ApiResponse[AskResponse],
    summary="Ask a question about an indexed repository",
    description=(
        "Runs the full RAG flow: semantic retrieval from the Qdrant "
        "collection, context construction under a token budget, grounded "
        "answer generation with Gemini, and heuristic quality evaluation."
    ),
    responses={
        400: {
            "description": "Repository path does not exist",
            "content": error_example(
                "invalid_repository_path", "Repository path does not exist: ..."
            ),
        },
        502: {
            "description": "The AI provider failed permanently",
            "content": error_example(
                "answer_generation_failed", "Gemini request failed."
            ),
        },
    },
)
def ask_question(
    request: AskRequest,
    service: AIService = Depends(get_ai_service),
) -> ApiResponse[AskResponse]:
    """Answer a question about an indexed repository."""
    try:
        outcome = service.ask(
            repository_path=request.repository_path,
            collection_name=request.collection_name,
            question=request.question,
            top_k=request.top_k,
            max_context_tokens=request.max_context_tokens,
            temperature=request.temperature,
        )
    except ScanError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_repository_path", "message": str(exc)},
        ) from exc
    except AnswerGenerationError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "answer_generation_failed", "message": str(exc)},
        ) from exc

    data = AskResponse(
        answer=outcome.response.answer,
        confidence=outcome.evaluation.confidence,
        referenced_files=outcome.response.referenced_files,
        retrieved_chunks=outcome.retrieval.total_found,
        context_tokens=outcome.context.statistics.total_tokens,
        warnings=outcome.evaluation.warnings,
        generation_time=outcome.response.generation_time,
    )
    return ApiResponse(data=data, message="Question answered.")

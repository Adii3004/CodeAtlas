"""System endpoints: lightweight status and diagnostics."""

import logging
import socket
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from qdrant_client import QdrantClient

from ai.provider import GeminiProvider
from api.dependencies import get_embedding_cache, get_qdrant_client
from api.envelope import ApiResponse
from config.settings import Settings, get_settings
from embeddings.cache import EmbeddingCache
from embeddings.provider import GeminiEmbeddingProvider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])

_STARTED_AT = time.monotonic()


class ApplicationStatus(BaseModel):
    version: str
    api_version: str
    uptime_seconds: float


class InfrastructureStatus(BaseModel):
    postgres_reachable: bool
    qdrant_reachable: bool


class AIStatus(BaseModel):
    gemini_configured: bool
    embedding_model: str
    llm_model: str


class StatisticsStatus(BaseModel):
    embedding_cache_entries: int
    available_collections: list[str]


class StatusResponse(BaseModel):
    application: ApplicationStatus
    infrastructure: InfrastructureStatus
    ai: AIStatus
    statistics: StatisticsStatus


def _postgres_reachable(settings: Settings) -> bool:
    try:
        with socket.create_connection(
            (settings.postgres_host, settings.postgres_port), timeout=1.0
        ):
            return True
    except OSError:
        return False


@router.get(
    "/status",
    response_model=ApiResponse[StatusResponse],
    summary="Service status",
    description=(
        "Lightweight status snapshot: application version and uptime, "
        "infrastructure reachability (PostgreSQL, Qdrant), AI configuration, "
        "and index statistics. Performs no heavy work."
    ),
)
def get_status(
    settings: Settings = Depends(get_settings),
    client: QdrantClient = Depends(get_qdrant_client),
    cache: EmbeddingCache = Depends(get_embedding_cache),
) -> ApiResponse[StatusResponse]:
    """Return the lightweight service status snapshot."""
    try:
        collections = [
            collection.name for collection in client.get_collections().collections
        ]
        qdrant_reachable = True
    except Exception as exc:
        logger.warning("qdrant unreachable during status check: %s", exc)
        collections = []
        qdrant_reachable = False

    data = StatusResponse(
        application=ApplicationStatus(
            version=settings.app_version,
            api_version="v1",
            uptime_seconds=round(time.monotonic() - _STARTED_AT, 1),
        ),
        infrastructure=InfrastructureStatus(
            postgres_reachable=_postgres_reachable(settings),
            qdrant_reachable=qdrant_reachable,
        ),
        ai=AIStatus(
            gemini_configured=bool(settings.gemini_api_key),
            embedding_model=GeminiEmbeddingProvider.model_name,
            llm_model=GeminiProvider.model_name,
        ),
        statistics=StatisticsStatus(
            embedding_cache_entries=len(cache),
            available_collections=sorted(collections),
        ),
    )
    return ApiResponse(data=data, message="Status collected.")

"""Core API routes: root and health check."""

import logging

from fastapi import APIRouter, Depends

from api.envelope import ApiResponse
from api.schemas import HealthResponse, RootResponse
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System"])


@router.get(
    "/",
    response_model=ApiResponse[RootResponse],
    summary="API information",
    description="Basic application information and useful links.",
)
def read_root(
    settings: Settings = Depends(get_settings),
) -> ApiResponse[RootResponse]:
    """Return basic application information and useful links."""
    data = RootResponse(
        message=f"Welcome to the {settings.app_name} API",
        app_name=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        health_url="/health",
    )
    return ApiResponse(data=data, message="OK")


@router.get(
    "/health",
    response_model=ApiResponse[HealthResponse],
    summary="Health check",
    description="Reports service health for monitoring and readiness checks.",
)
def read_health(
    settings: Settings = Depends(get_settings),
) -> ApiResponse[HealthResponse]:
    """Report service health for monitoring and readiness checks."""
    data = HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )
    return ApiResponse(data=data, message="OK")

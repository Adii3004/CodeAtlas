"""CodeAtlas backend entry point.

Run from the ``backend/`` directory with:

    uvicorn main:app --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.ask_routes import router as ask_router
from api.envelope import error_body
from api.repository_routes import router as repository_router
from api.routes import router as core_router
from api.system_routes import router as system_router
from config.settings import get_settings
from utils.logging import configure_logging

logger = logging.getLogger(__name__)

_TAGS_METADATA = [
    {
        "name": "Repository",
        "description": "Scan, analyze, and index local repositories.",
    },
    {
        "name": "AI",
        "description": "Grounded question answering over indexed repositories.",
    },
    {"name": "System", "description": "Service information, health, and status."},
]


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=_TAGS_METADATA,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(core_router)
    app.include_router(system_router)
    app.include_router(repository_router)
    app.include_router(ask_router)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict):
            error = str(detail.get("error", "http_error"))
            message = str(detail.get("message", ""))
        else:
            error, message = "http_error", str(detail)
        return JSONResponse(
            status_code=exc.status_code, content=error_body(error, message)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
            for err in exc.errors()
        )
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", problems),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Never leak stack traces to clients; log them server-side instead.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_body(
                "internal_error",
                "An unexpected error occurred. See server logs.",
            ),
        )

    logger.info("%s v%s initialized", settings.app_name, settings.app_version)
    return app


app = create_app()

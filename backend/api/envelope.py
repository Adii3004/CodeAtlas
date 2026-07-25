"""Shared response envelope used by every endpoint.

Success:  {"success": true,  "data": {...}, "error": null,  "message": "..."}
Failure:  {"success": false, "data": null,  "error": "code", "message": "..."}
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: str | None = None
    message: str = ""


def error_body(error: str, message: str) -> dict:
    """Plain-dict error envelope for exception handlers."""
    return {"success": False, "data": None, "error": error, "message": message}


def error_example(error: str, message: str) -> dict:
    """OpenAPI example payload for an error response."""
    return {"application/json": {"example": error_body(error, message)}}

"""Response schemas for the core API endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str


class RootResponse(BaseModel):
    message: str
    app_name: str
    version: str
    docs_url: str
    health_url: str

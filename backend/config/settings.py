"""Application settings backed by pydantic-settings.

App-level values can be overridden via environment variables prefixed with
``CODEATLAS_`` (e.g. ``CODEATLAS_DEBUG=true``). Infrastructure values
(PostgreSQL, Qdrant) use the same unprefixed names as docker-compose so a
single ``.env`` file at the project root drives both. ``../.env`` is loaded
first (project root, relative to ``backend/``), then ``backend/.env`` may
override it.
"""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_prefix="CODEATLAS_",
        extra="ignore",
    )

    app_name: str = "CodeAtlas"
    app_description: str = "Backend API for CodeAtlas, a codebase exploration tool."
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Origins allowed by CORS; defaults cover the Vite dev server.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # PostgreSQL connection settings (not used by the app yet — Step 1.3
    # only provisions the infrastructure). Unprefixed aliases match the
    # variable names docker-compose consumes.
    postgres_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("POSTGRES_HOST", "CODEATLAS_POSTGRES_HOST"),
    )
    postgres_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("POSTGRES_PORT", "CODEATLAS_POSTGRES_PORT"),
    )
    postgres_user: str = Field(
        default="codeatlas",
        validation_alias=AliasChoices("POSTGRES_USER", "CODEATLAS_POSTGRES_USER"),
    )
    postgres_password: str = Field(
        default="codeatlas_dev_password",
        validation_alias=AliasChoices(
            "POSTGRES_PASSWORD", "CODEATLAS_POSTGRES_PASSWORD"
        ),
    )
    postgres_db: str = Field(
        default="codeatlas",
        validation_alias=AliasChoices("POSTGRES_DB", "CODEATLAS_POSTGRES_DB"),
    )

    # Gemini API key for embeddings (never committed; set via environment
    # or .env).
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "CODEATLAS_GEMINI_API_KEY"),
    )

    # Qdrant connection settings (not used by the app yet).
    qdrant_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("QDRANT_HOST", "CODEATLAS_QDRANT_HOST"),
    )
    qdrant_http_port: int = Field(
        default=6333,
        validation_alias=AliasChoices("QDRANT_HTTP_PORT", "CODEATLAS_QDRANT_HTTP_PORT"),
    )
    qdrant_grpc_port: int = Field(
        default=6334,
        validation_alias=AliasChoices("QDRANT_GRPC_PORT", "CODEATLAS_QDRANT_GRPC_PORT"),
    )

    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL connection string (for future database integration)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def qdrant_url(self) -> str:
        """Qdrant HTTP endpoint URL (for future vector store integration)."""
        return f"http://{self.qdrant_host}:{self.qdrant_http_port}"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()

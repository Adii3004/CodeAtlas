"""Internal backend self-check: pass/fail per subsystem, nothing more."""

import logging
import socket
import tempfile
from pathlib import Path
from typing import ClassVar

from qdrant_client import QdrantClient

from chunking.builder import ChunkBuilder
from config.settings import get_settings
from embeddings.provider import EmbeddingProvider
from knowledge.builder import build_repository_knowledge
from parsers.models import ParseStatus
from parsers.python_parser import PythonParser
from retrieval.retriever import SemanticRetriever
from scanner.repository_scanner import RepositoryScanner

logger = logging.getLogger(__name__)


class _StubEmbeddings(EmbeddingProvider):
    """Never called: the retriever check queries a missing collection."""

    model_name: ClassVar[str] = "self-check-stub"
    dimension: ClassVar[int] = 1

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]


def run_self_check(qdrant_client: QdrantClient | None = None) -> dict[str, bool]:
    """Verify each subsystem works; returns pass/fail only."""
    settings = get_settings()
    checks: dict[str, bool] = {}

    with tempfile.TemporaryDirectory() as tmp:
        sample = Path(tmp) / "sample.py"
        sample.write_text("def ok():\n    return 1\n", encoding="utf-8")

        try:
            scan_result = RepositoryScanner().scan(tmp)
            checks["scanner"] = scan_result.total_files == 1
        except Exception:
            checks["scanner"] = False
            scan_result = None

        try:
            parse = PythonParser().parse(scan_result.files[0])  # type: ignore[union-attr]
            checks["parser"] = parse.status is ParseStatus.SUCCESS
        except Exception:
            checks["parser"] = False

        try:
            knowledge = build_repository_knowledge(scan_result)  # type: ignore[arg-type]
            chunks = ChunkBuilder().build(knowledge)
            checks["chunk_builder"] = chunks.total_chunks > 0
        except Exception:
            checks["chunk_builder"] = False

    try:
        client = qdrant_client or QdrantClient(url=settings.qdrant_url)
        client.get_collections()
        checks["qdrant"] = True
    except Exception:
        checks["qdrant"] = False
        client = None

    try:
        if client is None:
            checks["retriever"] = False
        else:
            result = SemanticRetriever(
                _StubEmbeddings(), "codeatlas_self_check_missing", client
            ).retrieve("self check")
            checks["retriever"] = result.is_empty
    except Exception:
        checks["retriever"] = False

    checks["gemini_configured"] = bool(settings.gemini_api_key)

    try:
        with socket.create_connection(
            (settings.postgres_host, settings.postgres_port), timeout=1.0
        ):
            checks["postgresql"] = True
    except OSError:
        checks["postgresql"] = False

    logger.info("self-check results: %s", checks)
    return checks

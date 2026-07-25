"""API tests for /graph, /report, /status, OpenAPI, response consistency,
and the internal self-check. No external services, no real Gemini."""

import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from api.dependencies import (  # noqa: E402
    get_embedding_cache,
    get_embedding_provider,
    get_qdrant_client,
)
from config.settings import get_settings  # noqa: E402
from embeddings.cache import EmbeddingCache  # noqa: E402
from embeddings.provider import EmbeddingProvider  # noqa: E402
from main import create_app  # noqa: E402
from services.self_check import run_self_check  # noqa: E402


class FakeProvider(EmbeddingProvider):
    model_name: ClassVar[str] = "fake-embedding-001"
    dimension: ClassVar[int] = 8

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [
            [b / 255.0 for b in hashlib.sha256(t.encode()).digest()[:8]] for t in texts
        ]


class UnreachableQdrant:
    """Stands in for a Qdrant client whose server is down."""

    def get_collections(self):
        raise ConnectionError("qdrant unreachable")


def _fake_settings(**overrides) -> SimpleNamespace:
    base = {
        "app_name": "CodeAtlas",
        "app_version": "0.1.0",
        "gemini_api_key": "test-key",
        "postgres_host": "127.0.0.1",
        "postgres_port": 1,  # closed port: postgres_reachable is False
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture
def qdrant() -> QdrantClient:
    return QdrantClient(":memory:")


@pytest.fixture
def client(qdrant: QdrantClient, tmp_path: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_embedding_provider] = lambda: FakeProvider()
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant
    app.dependency_overrides[get_embedding_cache] = lambda: EmbeddingCache(
        tmp_path / "cache.json"
    )
    app.dependency_overrides[get_settings] = lambda: _fake_settings()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "sample_repo"
    root.mkdir()
    (root / "core.py").write_text("C = 1\n", encoding="utf-8")
    (root / "app.py").write_text(
        "import core\n\ndef main():\n    pass\n", encoding="utf-8"
    )
    return root


class TestGraphEndpoint:
    def test_graph_returns_nodes_edges_statistics(
        self, client: TestClient, repo: Path
    ) -> None:
        response = client.get("/graph", params={"repository_path": str(repo)})

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["repository_name"] == "sample_repo"
        assert {n["id"] for n in data["nodes"]} == {"app.py", "core.py"}
        assert [(e["source"], e["target"]) for e in data["edges"]] == [
            ("app.py", "core.py")
        ]
        node = data["nodes"][0]
        for field in ("label", "category", "language", "x", "y", "group"):
            assert field in node
        stats = data["statistics"]
        assert stats["nodes"] == 2
        assert stats["edges"] == 1
        assert stats["cycles"] == 0

    def test_graph_invalid_path(self, client: TestClient) -> None:
        response = client.get("/graph", params={"repository_path": "C:/nope"})
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_repository_path"

    def test_graph_missing_param(self, client: TestClient) -> None:
        response = client.get("/graph")
        assert response.status_code == 422
        assert response.json()["error"] == "validation_error"


class TestReportEndpoint:
    def test_report_returns_full_repository_report(
        self, client: TestClient, repo: Path
    ) -> None:
        response = client.get("/report", params={"repository_path": str(repo)})

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["general"]["repository_name"] == "sample_repo"
        assert data["general"]["total_files"] == 2
        assert data["languages"] == {"python": 2}
        assert data["graph_summary"]["nodes"] == 2
        assert data["architecture"]["root_modules"] == ["app.py"]
        assert data["issues"]["circular_dependencies"] == []

    def test_report_invalid_path(self, client: TestClient) -> None:
        response = client.get("/report", params={"repository_path": "C:/nope"})
        assert response.status_code == 400


class TestStatusEndpoint:
    def test_status_healthy(self, client: TestClient) -> None:
        response = client.get("/status")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["application"]["version"] == "0.1.0"
        assert data["application"]["api_version"] == "v1"
        assert data["application"]["uptime_seconds"] >= 0
        assert data["infrastructure"]["qdrant_reachable"] is True
        assert data["infrastructure"]["postgres_reachable"] is False  # port 1
        assert data["ai"]["gemini_configured"] is True
        assert data["ai"]["embedding_model"] == "gemini-embedding-001"
        assert data["ai"]["llm_model"] == "gemini-2.5-flash"
        assert data["statistics"]["embedding_cache_entries"] == 0
        assert data["statistics"]["available_collections"] == []

    def test_status_with_unreachable_qdrant(self, client: TestClient) -> None:
        client.app.dependency_overrides[get_qdrant_client] = lambda: UnreachableQdrant()

        response = client.get("/status")

        assert response.status_code == 200  # status itself must not fail
        data = response.json()["data"]
        assert data["infrastructure"]["qdrant_reachable"] is False
        assert data["statistics"]["available_collections"] == []

    def test_status_gemini_not_configured(self, client: TestClient) -> None:
        client.app.dependency_overrides[get_settings] = lambda: _fake_settings(
            gemini_api_key=None
        )

        response = client.get("/status")

        assert response.json()["data"]["ai"]["gemini_configured"] is False

    def test_status_lists_collections(
        self, client: TestClient, qdrant: QdrantClient
    ) -> None:
        from qdrant_client.models import Distance, VectorParams

        qdrant.create_collection(
            "codeatlas_demo",
            vectors_config=VectorParams(size=8, distance=Distance.COSINE),
        )

        response = client.get("/status")

        assert response.json()["data"]["statistics"]["available_collections"] == [
            "codeatlas_demo"
        ]


class TestOpenAPI:
    def test_openapi_generates(self, client: TestClient) -> None:
        response = client.get("/openapi.json")

        assert response.status_code == 200
        spec = response.json()
        for path in (
            "/scan",
            "/index",
            "/ask",
            "/graph",
            "/report",
            "/status",
            "/health",
            "/",
        ):
            assert path in spec["paths"], f"missing {path}"

    def test_endpoints_have_summaries_and_tags(self, client: TestClient) -> None:
        spec = client.get("/openapi.json").json()

        tag_names = {tag["name"] for tag in spec["tags"]}
        assert {"Repository", "AI", "System"} <= tag_names

        for path, methods in spec["paths"].items():
            for operation in methods.values():
                assert operation.get("summary"), f"{path} missing summary"
                assert operation.get("description"), f"{path} missing description"
                assert operation.get("tags"), f"{path} missing tags"

    def test_request_examples_present(self, client: TestClient) -> None:
        spec = client.get("/openapi.json").json()
        schemas = spec["components"]["schemas"]
        for name in ("ScanRequest", "IndexRequest", "AskRequest"):
            assert "examples" in schemas[name], f"{name} missing examples"


class TestResponseConsistency:
    def test_all_endpoints_share_envelope(self, client: TestClient, repo: Path) -> None:
        envelope_keys = {"success", "data", "error", "message"}
        responses = [
            client.get("/"),
            client.get("/health"),
            client.get("/status"),
            client.get("/graph", params={"repository_path": str(repo)}),
            client.get("/report", params={"repository_path": str(repo)}),
            client.post("/scan", json={"repository_path": str(repo)}),
        ]
        for response in responses:
            assert response.status_code == 200
            assert set(response.json().keys()) == envelope_keys

    def test_error_responses_share_envelope(self, client: TestClient) -> None:
        error_responses = [
            client.post("/scan", json={"repository_path": "C:/nope"}),  # 400
            client.post("/scan", json={}),  # 422
            client.get("/graph"),  # 422
        ]
        for response in error_responses:
            body = response.json()
            assert set(body.keys()) == {"success", "data", "error", "message"}
            assert body["success"] is False
            assert body["data"] is None
            assert body["error"]


class TestSelfCheck:
    def test_self_check_passes_with_working_subsystems(
        self, qdrant: QdrantClient
    ) -> None:
        checks = run_self_check(qdrant_client=qdrant)

        assert checks["scanner"] is True
        assert checks["parser"] is True
        assert checks["chunk_builder"] is True
        assert checks["qdrant"] is True
        assert checks["retriever"] is True
        # Environment-dependent checks are present and boolean.
        assert isinstance(checks["gemini_configured"], bool)
        assert isinstance(checks["postgresql"], bool)

    def test_self_check_reports_qdrant_failure(self) -> None:
        checks = run_self_check(qdrant_client=UnreachableQdrant())  # type: ignore[arg-type]

        assert checks["qdrant"] is False
        assert checks["retriever"] is False
        assert checks["scanner"] is True  # unaffected subsystems still pass

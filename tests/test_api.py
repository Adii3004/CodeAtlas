"""API tests for the scan and index endpoints.

Uses FastAPI TestClient with the embedding provider mocked and Qdrant in
in-memory mode — no external services and no API calls.
"""

import hashlib
import sys
from pathlib import Path
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
from embeddings.cache import EmbeddingCache  # noqa: E402
from embeddings.provider import EmbeddingProvider  # noqa: E402
from main import create_app  # noqa: E402


class FakeProvider(EmbeddingProvider):
    model_name: ClassVar[str] = "fake-embedding-001"
    dimension: ClassVar[int] = 8

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [
            [b / 255.0 for b in hashlib.sha256(t.encode()).digest()[:8]] for t in texts
        ]


class BrokenProvider(FakeProvider):
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise ConnectionError("provider down")


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
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "sample_repo"
    root.mkdir()
    (root / "models.py").write_text("class Model:\n    pass\n", encoding="utf-8")
    (root / "app.py").write_text(
        "import models\n\ndef main():\n    pass\n", encoding="utf-8"
    )
    (root / "README.md").write_text("# Sample\nDocs.\n", encoding="utf-8")
    return root


class TestScan:
    def test_successful_scan(self, client: TestClient, repo: Path) -> None:
        response = client.post("/scan", json={"repository_path": str(repo)})

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["error"] is None
        data = body["data"]
        assert data["repository_name"] == "sample_repo"
        assert data["total_files"] == 3
        assert data["parsed_files"] == 2
        assert data["total_symbols"] == 2  # Model, main
        assert data["total_imports"] == 1
        assert data["languages"]["python"] == 2
        assert data["graph"]["nodes"] == 3
        assert data["graph"]["edges"] == 1
        assert data["graph"]["cycles"] == 0
        assert data["report"]["circular_dependencies"] == 0

    def test_scan_without_graph_and_report(
        self, client: TestClient, repo: Path
    ) -> None:
        response = client.post(
            "/scan",
            json={
                "repository_path": str(repo),
                "build_graph": False,
                "build_report": False,
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["graph"] is None
        assert data["report"] is None

    def test_invalid_repository_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/scan", json={"repository_path": "C:/definitely/not/here"}
        )

        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"] == "invalid_repository_path"
        assert "does not exist" in body["message"]
        assert "Traceback" not in response.text

    def test_missing_path_returns_422(self, client: TestClient) -> None:
        response = client.post("/scan", json={})

        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["error"] == "validation_error"
        assert "repository_path" in body["message"]

    def test_file_as_path_returns_400(self, client: TestClient, repo: Path) -> None:
        response = client.post("/scan", json={"repository_path": str(repo / "app.py")})
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_repository_path"


class TestIndex:
    def test_successful_indexing(
        self, client: TestClient, repo: Path, qdrant: QdrantClient
    ) -> None:
        response = client.post(
            "/index",
            json={"repository_path": str(repo), "collection_name": "test_coll"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["collection_name"] == "test_coll"
        assert data["embedding_model"] == "fake-embedding-001"
        assert data["total_chunks"] > 0
        assert data["indexed_chunks"] == data["total_chunks"]
        assert data["cached_chunks"] == 0
        assert data["failed_chunks"] == 0
        assert qdrant.count("test_coll", exact=True).count == data["total_chunks"]

    def test_second_indexing_hits_cache(self, client: TestClient, repo: Path) -> None:
        first = client.post(
            "/index",
            json={"repository_path": str(repo), "collection_name": "test_coll"},
        ).json()["data"]
        second = client.post(
            "/index",
            json={"repository_path": str(repo), "collection_name": "test_coll"},
        ).json()["data"]

        assert second["cached_chunks"] == first["total_chunks"]
        assert second["indexed_chunks"] == 0

    def test_default_collection_name(self, client: TestClient, repo: Path) -> None:
        response = client.post("/index", json={"repository_path": str(repo)})

        assert response.status_code == 200
        assert response.json()["data"]["collection_name"] == "codeatlas_sample_repo"

    def test_rebuild_drops_and_recreates(
        self, client: TestClient, repo: Path, qdrant: QdrantClient
    ) -> None:
        client.post(
            "/index",
            json={"repository_path": str(repo), "collection_name": "test_coll"},
        )
        (repo / "README.md").unlink()
        response = client.post(
            "/index",
            json={
                "repository_path": str(repo),
                "collection_name": "test_coll",
                "rebuild": True,
            },
        )

        assert response.status_code == 200
        total = response.json()["data"]["total_chunks"]
        assert qdrant.count("test_coll", exact=True).count == total

    def test_indexing_failure_returns_502(self, client: TestClient, repo: Path) -> None:
        client.app.dependency_overrides[get_embedding_provider] = lambda: (
            BrokenProvider()
        )

        response = client.post(
            "/index",
            json={"repository_path": str(repo), "collection_name": "test_coll"},
        )

        assert response.status_code == 502
        body = response.json()
        assert body["success"] is False
        assert body["error"] == "embedding_failed"
        assert "Traceback" not in response.text

    def test_index_invalid_path_returns_400(self, client: TestClient) -> None:
        response = client.post("/index", json={"repository_path": "Z:/nope"})
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_repository_path"

    def test_index_missing_path_returns_422(self, client: TestClient) -> None:
        response = client.post("/index", json={"rebuild": True})
        assert response.status_code == 422
        assert response.json()["error"] == "validation_error"


class TestErrorShape:
    def test_unhandled_errors_are_structured(
        self, client: TestClient, repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from services.repository_service import RepositoryService

        def boom(self, path: str):
            raise RuntimeError("secret internal detail")

        monkeypatch.setattr(RepositoryService, "build_knowledge", boom)

        response = client.post("/scan", json={"repository_path": str(repo)})

        assert response.status_code == 500
        body = response.json()
        assert body["success"] is False
        assert body["error"] == "internal_error"
        assert "secret internal detail" not in response.text
        assert "Traceback" not in response.text

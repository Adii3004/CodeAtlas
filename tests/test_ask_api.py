"""API tests for POST /ask. Gemini and embeddings are always mocked."""

import hashlib
import sys
from pathlib import Path
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from ai.provider import AIProvider  # noqa: E402
from api.dependencies import (  # noqa: E402
    get_ai_service,
    get_embedding_cache,
    get_embedding_provider,
    get_qdrant_client,
)
from embeddings.cache import EmbeddingCache  # noqa: E402
from embeddings.provider import EmbeddingProvider  # noqa: E402
from main import create_app  # noqa: E402
from services.ai_service import AIService  # noqa: E402


class FakeEmbeddings(EmbeddingProvider):
    model_name: ClassVar[str] = "fake-embedding-001"
    dimension: ClassVar[int] = 8

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [
            [b / 255.0 for b in hashlib.sha256(t.encode()).digest()[:8]] for t in texts
        ]


class FakeAI(AIProvider):
    model_name: ClassVar[str] = "fake-ai-001"

    def __init__(self, answer: str = "It works via models.py.") -> None:
        self._answer = answer
        self.prompts: list[str] = []

    def generate(self, prompt: str, *, temperature: float) -> str:
        self.prompts.append(prompt)
        return self._answer


class BrokenAI(FakeAI):
    def generate(self, prompt: str, *, temperature: float) -> str:
        raise ConnectionError("gemini is down")


@pytest.fixture
def qdrant() -> QdrantClient:
    return QdrantClient(":memory:")


def _make_client(
    qdrant: QdrantClient, tmp_path: Path, ai_provider: AIProvider
) -> TestClient:
    app = create_app()
    embeddings = FakeEmbeddings()
    app.dependency_overrides[get_embedding_provider] = lambda: embeddings
    app.dependency_overrides[get_qdrant_client] = lambda: qdrant
    app.dependency_overrides[get_embedding_cache] = lambda: EmbeddingCache(
        tmp_path / "cache.json"
    )
    app.dependency_overrides[get_ai_service] = lambda: AIService(
        embeddings, ai_provider, qdrant, sleep=lambda _: None
    )
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "sample_repo"
    root.mkdir()
    (root / "models.py").write_text(
        "class Model:\n    '''Data model.'''\n    pass\n", encoding="utf-8"
    )
    (root / "app.py").write_text(
        "import models\n\ndef main():\n    pass\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def client(qdrant: QdrantClient, tmp_path: Path) -> TestClient:
    return _make_client(qdrant, tmp_path, FakeAI())


def _index(client: TestClient, repo: Path, collection: str = "ask_coll") -> None:
    response = client.post(
        "/index",
        json={"repository_path": str(repo), "collection_name": collection},
    )
    assert response.status_code == 200


class TestSuccessfulAnswer:
    def test_answer_shape_and_content(self, client: TestClient, repo: Path) -> None:
        _index(client, repo)

        response = client.post(
            "/ask",
            json={
                "collection_name": "ask_coll",
                "repository_path": str(repo),
                "question": "what is the data model?",
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["answer"] == "It works via models.py."
        assert data["referenced_files"] == ["models.py"]
        assert data["retrieved_chunks"] > 0
        assert data["context_tokens"] > 0
        assert 0 <= data["confidence"] <= 100
        assert isinstance(data["warnings"], list)
        assert data["generation_time"] >= 0.0

    def test_custom_parameters_accepted(self, client: TestClient, repo: Path) -> None:
        _index(client, repo)

        response = client.post(
            "/ask",
            json={
                "collection_name": "ask_coll",
                "repository_path": str(repo),
                "question": "q",
                "top_k": 3,
                "max_context_tokens": 500,
                "temperature": 0.7,
            },
        )

        assert response.status_code == 200
        assert response.json()["data"]["retrieved_chunks"] <= 3


class TestEmptyRetrieval:
    def test_missing_collection_still_answers_with_warning(
        self, client: TestClient, repo: Path
    ) -> None:
        response = client.post(
            "/ask",
            json={
                "collection_name": "never_indexed",
                "repository_path": str(repo),
                "question": "anything?",
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["retrieved_chunks"] == 0
        assert "No chunks were retrieved for this query." in data["warnings"]
        assert data["confidence"] <= 30


class TestGeminiFailure:
    def test_provider_failure_returns_502(
        self, qdrant: QdrantClient, tmp_path: Path, repo: Path
    ) -> None:
        client = _make_client(qdrant, tmp_path, BrokenAI())
        _index(client, repo)

        response = client.post(
            "/ask",
            json={
                "collection_name": "ask_coll",
                "repository_path": str(repo),
                "question": "q",
            },
        )

        assert response.status_code == 502
        body = response.json()
        assert body["success"] is False
        assert body["error"] == "answer_generation_failed"
        assert "Traceback" not in response.text


class TestInvalidRepository:
    def test_invalid_path_returns_400(self, client: TestClient) -> None:
        response = client.post(
            "/ask",
            json={
                "collection_name": "ask_coll",
                "repository_path": "C:/definitely/not/here",
                "question": "q",
            },
        )

        assert response.status_code == 400
        body = response.json()
        assert body["success"] is False
        assert body["error"] == "invalid_repository_path"


class TestMalformedRequest:
    def test_missing_question_returns_422(self, client: TestClient, repo: Path) -> None:
        response = client.post(
            "/ask",
            json={"collection_name": "c", "repository_path": str(repo)},
        )
        assert response.status_code == 422

    def test_empty_question_returns_422(self, client: TestClient, repo: Path) -> None:
        response = client.post(
            "/ask",
            json={
                "collection_name": "c",
                "repository_path": str(repo),
                "question": "",
            },
        )
        assert response.status_code == 422

    @pytest.mark.parametrize(
        "overrides",
        [
            {"top_k": 0},
            {"top_k": 51},
            {"temperature": -0.1},
            {"temperature": 2.5},
            {"max_context_tokens": 10},
        ],
    )
    def test_out_of_range_parameters_return_422(
        self, client: TestClient, repo: Path, overrides: dict
    ) -> None:
        payload = {
            "collection_name": "c",
            "repository_path": str(repo),
            "question": "q",
            **overrides,
        }
        response = client.post("/ask", json=payload)
        assert response.status_code == 422

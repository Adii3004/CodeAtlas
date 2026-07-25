"""Embedding provider abstraction and the Gemini implementation."""

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

from config.settings import get_settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Turns batches of texts into embedding vectors.

    Implementations declare their model name and vector dimension as class
    attributes and implement one method. Transient failures may raise; the
    IndexBuilder is responsible for retries.
    """

    model_name: ClassVar[str]
    dimension: ClassVar[int]

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed each text; the result list matches the input order."""
        raise NotImplementedError


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Google Gemini embedding provider.

    Uses ``gemini-embedding-001`` (the successor of the retired
    ``text-embedding-004``) at 768 output dimensions. The google-genai
    client is created lazily so importing this module never requires
    credentials.
    """

    model_name: ClassVar[str] = "gemini-embedding-001"
    dimension: ClassVar[int] = 768

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or get_settings().gemini_api_key
        self._client: object | None = None

    def _get_client(self):  # noqa: ANN202 - external SDK type
        if self._client is None:
            from google import genai

            if not self._api_key:
                raise RuntimeError(
                    "Gemini API key is not configured. Set GEMINI_API_KEY in "
                    "the environment or .env file."
                )
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts with the Gemini embedding model."""
        from google.genai import types

        client = self._get_client()
        response = client.models.embed_content(
            model=self.model_name,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=self.dimension),
        )
        vectors = [list(embedding.values) for embedding in response.embeddings]
        logger.debug("Embedded batch of %d texts", len(texts))
        return vectors

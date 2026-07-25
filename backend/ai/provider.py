"""AI provider abstraction and the Gemini implementation."""

import logging
from abc import ABC, abstractmethod
from typing import ClassVar

from config.settings import get_settings

logger = logging.getLogger(__name__)

DEFAULT_TEMPERATURE = 0.2


class AIProvider(ABC):
    """Generates text completions for a prompt.

    Implementations may raise for transient failures; the AnswerGenerator
    is responsible for retries.
    """

    model_name: ClassVar[str]

    @abstractmethod
    def generate(self, prompt: str, *, temperature: float) -> str:
        """Return the model's answer text for the prompt."""
        raise NotImplementedError


class GeminiProvider(AIProvider):
    """Google Gemini 2.5 Flash provider.

    The google-genai client is created lazily so importing this module never
    requires credentials.
    """

    model_name: ClassVar[str] = "gemini-2.5-flash"

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

    def generate(self, prompt: str, *, temperature: float) -> str:
        """Generate an answer with Gemini 2.5 Flash."""
        from google.genai import types

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        text = response.text or ""
        logger.debug("Gemini returned %d characters", len(text))
        return text

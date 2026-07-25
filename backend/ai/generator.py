"""AnswerGenerator: produces a grounded AIResponse for one query."""

import logging
import re
import time
from collections.abc import Callable

from ai.models import AIResponse
from ai.prompts import PromptBuilder
from ai.provider import DEFAULT_TEMPERATURE, AIProvider
from chunking.models import estimate_tokens
from context.models import LLMContext

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.0


class AnswerGenerator:
    """Builds the prompt, calls the provider with retries, and packages
    the result."""

    def __init__(
        self,
        provider: AIProvider,
        prompt_builder: PromptBuilder | None = None,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._provider = provider
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._temperature = temperature
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep

    def answer(self, query: str, context: LLMContext) -> AIResponse:
        """Generate one grounded answer for the query."""
        prompt = self._prompt_builder.build(query, context)
        start = time.perf_counter()
        answer_text = self._generate_with_retry(prompt)
        elapsed = round(time.perf_counter() - start, 3)

        prompt_tokens = estimate_tokens(prompt)
        completion_tokens = estimate_tokens(answer_text)
        response = AIResponse(
            answer=answer_text,
            model=self._provider.model_name,
            prompt_tokens_estimate=prompt_tokens,
            completion_tokens_estimate=completion_tokens,
            total_tokens_estimate=prompt_tokens + completion_tokens,
            referenced_files=_referenced_files(answer_text, context),
            generation_time=elapsed,
        )
        logger.info(
            "Answer generated (%s): %d prompt + %d completion tokens in %.2fs",
            response.model,
            prompt_tokens,
            completion_tokens,
            elapsed,
        )
        return response

    def _generate_with_retry(self, prompt: str) -> str:
        """Call the provider, retrying transient failures with backoff."""
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return self._provider.generate(prompt, temperature=self._temperature)
            except Exception as exc:
                last_error = exc
                if attempt + 1 < self._max_retries:
                    delay = self._backoff_seconds * (2**attempt)
                    logger.warning(
                        "Generation attempt %d/%d failed (%s); retrying in %.1fs",
                        attempt + 1,
                        self._max_retries,
                        exc,
                        delay,
                    )
                    self._sleep(delay)
        assert last_error is not None
        raise last_error


def _referenced_files(answer: str, context: LLMContext) -> list[str]:
    """Context file paths that the answer actually mentions.

    A file counts as referenced when its relative path appears in the
    answer, or its bare filename appears at a clean boundary (so
    ``models.py`` does not falsely match inside ``other/models.py``).
    """
    referenced: list[str] = []
    seen: set[str] = set()
    for section in context.sections:
        for chunk in section.chunks:
            path = chunk.relative_path
            if path in seen or path == ".":
                continue
            filename = path.rsplit("/", 1)[-1]
            bare_name = re.compile(r"(?<![\w/\\])" + re.escape(filename))
            if path in answer or bare_name.search(answer):
                seen.add(path)
                referenced.append(path)
    return sorted(referenced)

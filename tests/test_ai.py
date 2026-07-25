"""Unit tests for AI answer generation. Gemini is always mocked."""

from datetime import datetime
from typing import ClassVar

import pytest

from ai import AIProvider, AIResponse, AnswerGenerator, PromptBuilder
from ai.prompts import NO_CONTEXT_MARKER, SYSTEM_INSTRUCTIONS
from chunking import ChunkType
from context.models import (
    ContextChunk,
    ContextSection,
    ContextStatistics,
    LLMContext,
)


class FakeAIProvider(AIProvider):
    """Records prompts/temperatures and returns a canned answer."""

    model_name: ClassVar[str] = "fake-model-001"

    def __init__(self, answer: str = "The answer.") -> None:
        self.answer = answer
        self.prompts: list[str] = []
        self.temperatures: list[float] = []

    def generate(self, prompt: str, *, temperature: float) -> str:
        self.prompts.append(prompt)
        self.temperatures.append(temperature)
        return self.answer


class FlakyAIProvider(FakeAIProvider):
    def __init__(self, failures: int, answer: str = "Recovered.") -> None:
        super().__init__(answer)
        self._failures = failures

    def generate(self, prompt: str, *, temperature: float) -> str:
        if self._failures > 0:
            self._failures -= 1
            raise ConnectionError("transient")
        return super().generate(prompt, temperature=temperature)


def _chunk(
    path: str,
    content: str,
    symbol: str | None = None,
    chunk_type: ChunkType = ChunkType.FUNCTION,
) -> ContextChunk:
    return ContextChunk(
        chunk_id=f"id-{path}-{symbol}",
        relative_path=path,
        chunk_type=chunk_type,
        symbol_name=symbol,
        start_line=1,
        end_line=5,
        score=0.9,
        token_estimate=10,
        content=content,
    )


def _context(sections: list[ContextSection]) -> LLMContext:
    included = sum(len(s.chunks) for s in sections)
    tokens = sum(c.token_estimate for s in sections for c in s.chunks)
    return LLMContext(
        original_query="q",
        repository_name="testrepo",
        generated_at=datetime(2026, 7, 25, 12, 0, 0),
        total_chunks=included,
        estimated_tokens=tokens,
        sections=sections,
        statistics=ContextStatistics(
            included_chunks=included, skipped_chunks=0, total_tokens=tokens
        ),
    )


def _full_context() -> LLMContext:
    return _context(
        [
            ContextSection(
                title="Repository Summary",
                priority=1,
                chunks=[
                    _chunk(
                        ".",
                        "Repository: testrepo\nTotal files: 2",
                        chunk_type=ChunkType.FILE_SUMMARY,
                    )
                ],
            ),
            ContextSection(
                title="Relevant Functions",
                priority=4,
                chunks=[_chunk("src/service.py", "def run():\n    pass", "run")],
            ),
        ]
    )


class TestPromptConstruction:
    def test_prompt_contains_all_four_parts_in_order(self) -> None:
        prompt = PromptBuilder().build("where is run?", _full_context())

        positions = [
            prompt.index(SYSTEM_INSTRUCTIONS[:40]),
            prompt.index("## Repository Summary"),
            prompt.index("## Retrieved Context"),
            prompt.index("## User Question"),
        ]
        assert positions == sorted(positions)
        assert "where is run?" in prompt
        assert "Repository: testrepo" in prompt
        assert "def run():" in prompt
        assert "src/service.py :: run" in prompt

    def test_grounding_rules_present(self) -> None:
        prompt = PromptBuilder().build("q", _full_context())

        assert "ONLY using the context supplied below" in prompt
        assert "Never invent code" in prompt
        assert "does not contain enough information" in prompt
        assert "mention the file name" in prompt
        assert "reasoning clearly" in prompt


class TestMissingContext:
    def test_empty_context_gets_marker(self) -> None:
        prompt = PromptBuilder().build("q", _context([]))

        assert NO_CONTEXT_MARKER in prompt
        assert "(no repository summary available)" in prompt

    def test_summary_only_context(self) -> None:
        context = _context(
            [
                ContextSection(
                    title="Repository Summary",
                    priority=1,
                    chunks=[
                        _chunk(
                            ".",
                            "Repository: testrepo",
                            chunk_type=ChunkType.FILE_SUMMARY,
                        )
                    ],
                )
            ]
        )
        prompt = PromptBuilder().build("q", context)

        assert "Repository: testrepo" in prompt
        assert NO_CONTEXT_MARKER in prompt

    def test_generator_still_answers_on_empty_context(self) -> None:
        provider = FakeAIProvider(answer="I cannot find this in the context.")
        response = AnswerGenerator(provider, sleep=lambda _: None).answer(
            "q", _context([])
        )

        assert response.answer == "I cannot find this in the context."
        assert response.referenced_files == []


class TestProviderAbstraction:
    def test_temperature_default_is_02(self) -> None:
        provider = FakeAIProvider()
        AnswerGenerator(provider).answer("q", _full_context())

        assert provider.temperatures == [0.2]

    def test_temperature_configurable(self) -> None:
        provider = FakeAIProvider()
        AnswerGenerator(provider, temperature=0.7).answer("q", _full_context())

        assert provider.temperatures == [0.7]

    def test_model_name_from_provider(self) -> None:
        response = AnswerGenerator(FakeAIProvider()).answer("q", _full_context())
        assert response.model == "fake-model-001"

    def test_gemini_provider_declares_flash_model(self) -> None:
        from ai import GeminiProvider

        assert GeminiProvider.model_name == "gemini-2.5-flash"

    def test_gemini_without_key_raises_clear_error(self) -> None:
        from ai import GeminiProvider

        provider = GeminiProvider(api_key=None)
        provider._api_key = None  # force missing key regardless of env
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            provider.generate("hi", temperature=0.2)


class TestRetries:
    def test_transient_failures_retried_with_backoff(self) -> None:
        provider = FlakyAIProvider(failures=2)
        delays: list[float] = []
        generator = AnswerGenerator(
            provider, max_retries=3, backoff_seconds=1.0, sleep=delays.append
        )

        response = generator.answer("q", _full_context())

        assert response.answer == "Recovered."
        assert delays == [1.0, 2.0]

    def test_permanent_failure_raises_after_retries(self) -> None:
        provider = FlakyAIProvider(failures=99)
        delays: list[float] = []
        generator = AnswerGenerator(provider, max_retries=3, sleep=delays.append)

        with pytest.raises(ConnectionError):
            generator.answer("q", _full_context())
        assert len(delays) == 2


class TestResponseParsing:
    def test_response_fields(self) -> None:
        provider = FakeAIProvider(answer="The run function lives in src/service.py.")
        response = AnswerGenerator(provider).answer("where is run?", _full_context())

        assert isinstance(response, AIResponse)
        assert response.answer.startswith("The run function")
        assert response.prompt_tokens_estimate > 0
        assert response.completion_tokens_estimate > 0
        assert response.total_tokens_estimate == (
            response.prompt_tokens_estimate + response.completion_tokens_estimate
        )
        assert response.generation_time >= 0.0

    def test_referenced_files_extracted_from_answer(self) -> None:
        provider = FakeAIProvider(answer="See src/service.py for the implementation.")
        response = AnswerGenerator(provider).answer("q", _full_context())

        assert response.referenced_files == ["src/service.py"]

    def test_bare_filename_counts_as_reference(self) -> None:
        provider = FakeAIProvider(answer="Look at service.py.")
        response = AnswerGenerator(provider).answer("q", _full_context())

        assert response.referenced_files == ["src/service.py"]

    def test_unmentioned_files_not_referenced(self) -> None:
        provider = FakeAIProvider(answer="No files are relevant here.")
        response = AnswerGenerator(provider).answer("q", _full_context())

        assert response.referenced_files == []

    def test_same_filename_in_other_directory_not_referenced(self) -> None:
        # Context has src/service.py; the answer mentions other/service.py.
        # The bare filename inside a different path must not count.
        provider = FakeAIProvider(answer="See other/service.py instead.")
        response = AnswerGenerator(provider).answer("q", _full_context())

        assert response.referenced_files == []

    def test_response_serializes(self) -> None:
        response = AnswerGenerator(FakeAIProvider()).answer("q", _full_context())
        restored = AIResponse.model_validate_json(response.model_dump_json())
        assert restored.model == "fake-model-001"

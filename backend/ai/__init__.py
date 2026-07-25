"""AI package: grounded answer generation over the repository context.

Single-shot answering only — no chat, no history, no streaming.
"""

from ai.generator import AnswerGenerator
from ai.models import AIResponse
from ai.prompts import PromptBuilder
from ai.provider import AIProvider, GeminiProvider

__all__ = [
    "AIProvider",
    "AIResponse",
    "AnswerGenerator",
    "GeminiProvider",
    "PromptBuilder",
]

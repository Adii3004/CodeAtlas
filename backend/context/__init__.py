"""Context package: assembles LLM-ready context from retrieval results.

No LLM calls — this package only selects, orders, and budgets content.
"""

from context.builder import ContextBuilder
from context.models import (
    ContextChunk,
    ContextSection,
    ContextStatistics,
    LLMContext,
)

__all__ = [
    "ContextBuilder",
    "ContextChunk",
    "ContextSection",
    "ContextStatistics",
    "LLMContext",
]

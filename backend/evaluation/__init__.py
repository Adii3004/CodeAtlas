"""Evaluation package: heuristic quality assessment of RAG answers.

No LLM calls — every metric is computed deterministically from the
pipeline's own artifacts.
"""

from evaluation.evaluator import AnswerEvaluator
from evaluation.models import (
    EvaluationResult,
    GroundingStatistics,
    HallucinationCheck,
    RetrievalStatistics,
)

__all__ = [
    "AnswerEvaluator",
    "EvaluationResult",
    "GroundingStatistics",
    "HallucinationCheck",
    "RetrievalStatistics",
]

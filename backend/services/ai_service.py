"""AIService: the full question-answering flow behind POST /ask.

Exposes each stage (retrieve, build_context, generate_answer, evaluate) and
one composed ask() so routes never orchestrate.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from qdrant_client import QdrantClient

from ai.generator import AnswerGenerator
from ai.models import AIResponse
from ai.provider import AIProvider
from context.builder import ContextBuilder
from context.models import LLMContext
from embeddings.provider import EmbeddingProvider
from evaluation.evaluator import AnswerEvaluator
from evaluation.models import EvaluationResult
from knowledge.models import RepositoryKnowledge
from retrieval.models import RetrievalResult
from retrieval.retriever import SemanticRetriever
from services.repository_service import RepositoryService

logger = logging.getLogger(__name__)


class AnswerGenerationError(Exception):
    """The AI provider failed permanently while generating the answer."""


@dataclass
class AskOutcome:
    """Everything produced by one /ask flow."""

    response: AIResponse
    evaluation: EvaluationResult
    retrieval: RetrievalResult
    context: LLMContext


class AIService:
    """Orchestrates the ask flow; construction is dependency-injected."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        ai_provider: AIProvider,
        qdrant_client: QdrantClient,
        repository_service: RepositoryService | None = None,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._ai_provider = ai_provider
        self._client = qdrant_client
        self._repository_service = repository_service or RepositoryService()
        self._sleep = sleep

    def retrieve(
        self, question: str, collection_name: str, top_k: int = 10
    ) -> RetrievalResult:
        """Semantic retrieval over one Qdrant collection."""
        retriever = SemanticRetriever(
            self._embedding_provider, collection_name, self._client
        )
        return retriever.retrieve(question, top_k=top_k)

    def build_context(
        self,
        question: str,
        retrieval: RetrievalResult,
        knowledge: RepositoryKnowledge,
        max_tokens: int = 4000,
    ) -> LLMContext:
        """Ordered, budgeted context for the LLM."""
        return ContextBuilder(max_tokens=max_tokens).build(
            question, retrieval, knowledge
        )

    def generate_answer(
        self, question: str, context: LLMContext, temperature: float = 0.2
    ) -> AIResponse:
        """Generate one grounded answer.

        Raises AnswerGenerationError when the provider fails permanently.
        """
        generator = AnswerGenerator(
            self._ai_provider, temperature=temperature, sleep=self._sleep
        )
        try:
            return generator.answer(question, context)
        except Exception as exc:
            logger.error("answer generation failed permanently: %s", exc)
            raise AnswerGenerationError(str(exc)) from exc

    def evaluate(
        self,
        question: str,
        retrieval: RetrievalResult,
        context: LLMContext,
        response: AIResponse,
    ) -> EvaluationResult:
        """Heuristic quality assessment of one answer."""
        return AnswerEvaluator().evaluate(question, retrieval, context, response)

    def ask(
        self,
        *,
        repository_path: str,
        collection_name: str,
        question: str,
        top_k: int = 10,
        max_context_tokens: int = 4000,
        temperature: float = 0.2,
    ) -> AskOutcome:
        """Run the complete flow for one question.

        Raises ScanError for bad paths and AnswerGenerationError when the
        AI provider fails permanently.
        """
        knowledge = self._repository_service.build_knowledge(repository_path)
        retrieval = self.retrieve(question, collection_name, top_k)
        context = self.build_context(question, retrieval, knowledge, max_context_tokens)
        response = self.generate_answer(question, context, temperature)
        evaluation = self.evaluate(question, retrieval, context, response)
        logger.info(
            "ask complete repository=%s collection=%s retrieved_chunks=%d "
            "context_tokens=%d generation_time=%.2fs confidence=%d",
            repository_path,
            collection_name,
            retrieval.total_found,
            context.statistics.total_tokens,
            response.generation_time,
            evaluation.confidence,
        )
        return AskOutcome(
            response=response,
            evaluation=evaluation,
            retrieval=retrieval,
            context=context,
        )

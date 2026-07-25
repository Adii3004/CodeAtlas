"""Retrieval package: semantic search over indexed repository chunks.

No reranking, no LLM calls — pure vector similarity retrieval.
"""

from retrieval.models import ChunkPayload, RetrievalResult, RetrievedChunk
from retrieval.retriever import Retriever, SemanticRetriever

__all__ = [
    "ChunkPayload",
    "RetrievalResult",
    "RetrievedChunk",
    "Retriever",
    "SemanticRetriever",
]

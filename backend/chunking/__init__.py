"""Chunking package: splits repository knowledge into embeddable chunks.

No embeddings, no vector store, no LLM — only deterministic text chunks.
"""

from chunking.builder import ChunkBuilder
from chunking.models import Chunk, ChunkType, RepositoryChunks

__all__ = [
    "Chunk",
    "ChunkBuilder",
    "ChunkType",
    "RepositoryChunks",
]

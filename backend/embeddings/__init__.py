"""Embeddings package: chunk embedding and Qdrant indexing.

No retrieval and no chat — this package only turns RepositoryChunks into
indexed vectors.
"""

from embeddings.cache import EmbeddingCache
from embeddings.indexer import IndexBuilder, default_collection_name
from embeddings.models import IndexedRepository, IndexStatistics
from embeddings.provider import EmbeddingProvider, GeminiEmbeddingProvider
from embeddings.store import QdrantVectorStore, chunk_payload, point_id_for

__all__ = [
    "EmbeddingCache",
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
    "IndexBuilder",
    "IndexStatistics",
    "IndexedRepository",
    "QdrantVectorStore",
    "chunk_payload",
    "point_id_for",
    "default_collection_name",
]

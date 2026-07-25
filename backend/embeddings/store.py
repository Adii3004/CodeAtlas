"""Qdrant vector store wrapper and payload construction."""

import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from chunking.models import Chunk
from config.settings import get_settings

logger = logging.getLogger(__name__)

#: Stable namespace for deriving Qdrant point UUIDs from chunk ids.
_POINT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def point_id_for(chunk_id: str) -> str:
    """Deterministic Qdrant point UUID for a chunk id."""
    return str(uuid.uuid5(_POINT_NAMESPACE, chunk_id))


def chunk_payload(chunk: Chunk) -> dict:
    """Qdrant payload for one chunk (the vector is stored separately)."""
    return {
        "chunk_id": chunk.chunk_id,
        "repository_name": chunk.repository_name,
        "relative_path": chunk.relative_path,
        "chunk_type": chunk.chunk_type.value,
        "language": chunk.language.value,
        "category": chunk.category.value,
        "symbol_name": chunk.symbol_name,
        "qualified_name": chunk.qualified_name,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "imports": chunk.imports,
        "dependencies": chunk.dependencies,
        "token_estimate": chunk.token_estimate,
    }


class QdrantVectorStore:
    """Thin wrapper around the Qdrant client used by the indexer."""

    def __init__(self, client: QdrantClient | None = None) -> None:
        if client is None:
            settings = get_settings()
            client = QdrantClient(url=settings.qdrant_url)
        self._client = client

    def ensure_collection(self, name: str, dimension: int) -> None:
        """Create the collection if it does not exist yet."""
        if self._client.collection_exists(name):
            return
        self._client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection %s (dim=%d)", name, dimension)

    def upsert_chunks(
        self,
        collection: str,
        chunks: list[Chunk],
        vectors: list[list[float]],
    ) -> None:
        """Write one point per chunk; vectors align with chunks by index."""
        points = [
            PointStruct(
                id=point_id_for(chunk.chunk_id),
                vector=vector,
                payload=chunk_payload(chunk),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self._client.upsert(collection_name=collection, points=points)
        logger.info("Upserted %d points into %s", len(points), collection)

    def count(self, collection: str) -> int:
        """Number of points currently stored in the collection."""
        return self._client.count(collection, exact=True).count

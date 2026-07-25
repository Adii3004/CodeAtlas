"""Embedding cache keyed by chunk_id + content hash.

A changed chunk (same id, different content) misses the cache; an unchanged
chunk is never re-embedded. Optionally persisted to a JSON file.
"""

import hashlib
import json
import logging
from pathlib import Path

from chunking.models import Chunk

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """In-memory embedding cache with optional JSON-file persistence."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._entries: dict[str, list[float]] = {}
        if path is not None and path.exists():
            try:
                self._entries = json.loads(path.read_text(encoding="utf-8"))
                logger.info(
                    "Loaded %d cached embeddings from %s", len(self._entries), path
                )
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Ignoring unreadable cache %s: %s", path, exc)

    @staticmethod
    def key_for(chunk: Chunk) -> str:
        """Cache key: chunk id + hash of its content."""
        content_hash = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()[:16]
        return f"{chunk.chunk_id}:{content_hash}"

    def get(self, key: str) -> list[float] | None:
        """Return the cached vector for a key, or None."""
        return self._entries.get(key)

    def set(self, key: str, vector: list[float]) -> None:
        """Store a vector under a key."""
        self._entries[key] = vector

    def __len__(self) -> int:
        return len(self._entries)

    def save(self) -> None:
        """Persist the cache if a path was configured."""
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._entries), encoding="utf-8")
        logger.debug("Saved %d cached embeddings to %s", len(self._entries), self._path)

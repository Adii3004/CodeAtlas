"""RepositoryService: the single orchestration layer for repository work.

Every route-facing repository operation lives here: scanning, knowledge,
graph, visualization, report, and indexing. Routes call these methods and
never orchestrate pipeline modules themselves.
"""

import logging
import time

from qdrant_client import QdrantClient

from chunking.builder import ChunkBuilder
from embeddings.cache import EmbeddingCache
from embeddings.indexer import IndexBuilder, default_collection_name
from embeddings.models import IndexedRepository
from embeddings.provider import EmbeddingProvider
from embeddings.store import QdrantVectorStore
from graph.analysis import RepositoryGraphAnalysis, analyze_graph
from graph.builder import DependencyGraphBuilder
from graph.models import RepositoryGraph
from graph.visualization import GraphVisualization, build_visualization
from knowledge.builder import build_repository_knowledge
from knowledge.models import RepositoryKnowledge
from reports.generator import ReportThresholds, generate_report
from reports.models import RepositoryReport
from scanner.models import ScanResult
from scanner.repository_scanner import RepositoryScanner

logger = logging.getLogger(__name__)


class RepositoryService:
    """Orchestrates the repository pipeline; construction is injectable.

    The embedding provider, Qdrant client, and cache are only required for
    :meth:`index`; scan/graph/report flows never touch them.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        qdrant_client: QdrantClient | None = None,
        embedding_cache: EmbeddingCache | None = None,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._qdrant_client = qdrant_client
        self._embedding_cache = embedding_cache

    def scan(self, repository_path: str) -> ScanResult:
        """Scan a repository path. Raises ScanError for invalid paths."""
        return RepositoryScanner().scan(repository_path)

    def build_knowledge(self, repository_path: str) -> RepositoryKnowledge:
        """Scan and build the unified knowledge model."""
        started = time.perf_counter()
        knowledge = build_repository_knowledge(self.scan(repository_path))
        logger.info(
            "knowledge built repository=%s files=%d parsed=%d elapsed=%.2fs",
            repository_path,
            knowledge.total_files,
            len(knowledge.parsed_files),
            time.perf_counter() - started,
        )
        return knowledge

    def build_graph(self, knowledge: RepositoryKnowledge) -> RepositoryGraph:
        """Build the dependency graph from knowledge."""
        return DependencyGraphBuilder().build(knowledge)

    def analyze(self, repository_graph: RepositoryGraph) -> RepositoryGraphAnalysis:
        """Analyze a dependency graph."""
        return analyze_graph(repository_graph)

    def build_visualization(
        self, repository_graph: RepositoryGraph
    ) -> GraphVisualization:
        """Build the draw-ready visualization model."""
        return build_visualization(repository_graph)

    def build_report(
        self,
        knowledge: RepositoryKnowledge,
        repository_graph: RepositoryGraph,
        analysis: RepositoryGraphAnalysis,
        thresholds: ReportThresholds | None = None,
    ) -> RepositoryReport:
        """Generate the repository report."""
        return generate_report(knowledge, repository_graph, analysis, thresholds)

    def index(
        self,
        repository_path: str,
        collection_name: str | None = None,
        rebuild: bool = False,
    ) -> IndexedRepository:
        """Scan, chunk, embed, and index a repository into Qdrant."""
        if self._embedding_provider is None or self._qdrant_client is None:
            raise RuntimeError(
                "RepositoryService.index requires an embedding provider and "
                "a Qdrant client."
            )
        knowledge = self.build_knowledge(repository_path)
        chunks = ChunkBuilder().build(knowledge)
        collection = collection_name or default_collection_name(
            knowledge.repository_name
        )
        if rebuild and self._qdrant_client.collection_exists(collection):
            self._qdrant_client.delete_collection(collection)
            logger.info("rebuild requested collection=%s dropped", collection)

        indexed = IndexBuilder(
            self._embedding_provider,
            QdrantVectorStore(client=self._qdrant_client),
            self._embedding_cache,
        ).build(chunks, collection)
        stats = indexed.statistics
        logger.info(
            "index complete repository=%s collection=%s chunks_indexed=%d "
            "cached=%d failed=%d elapsed=%.2fs",
            repository_path,
            collection,
            stats.embedded_chunks,
            stats.cached_chunks,
            stats.failed_chunks,
            stats.elapsed_seconds,
        )
        return indexed

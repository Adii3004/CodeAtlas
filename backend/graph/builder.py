"""Builds the repository dependency graph from RepositoryKnowledge."""

import logging

import networkx as nx

from graph.models import CODE_FILE_ATTR, RepositoryGraph, UnresolvedImport
from graph.resolver import ModuleResolver
from knowledge.models import RepositoryKnowledge

logger = logging.getLogger(__name__)


class DependencyGraphBuilder:
    """Turns a RepositoryKnowledge into a RepositoryGraph.

    Every repository file becomes a node; edges are added only for imports
    that resolve to another file inside the repository. Standard-library
    imports are skipped silently; everything else that fails to resolve is
    collected for diagnostics.
    """

    def build(self, knowledge: RepositoryKnowledge) -> RepositoryGraph:
        """Build the dependency graph for one repository."""
        graph = nx.DiGraph()
        for code_file in knowledge.files:
            graph.add_node(code_file.relative_path, **{CODE_FILE_ATTR: code_file})

        resolver = ModuleResolver(knowledge.files)
        unresolved: list[UnresolvedImport] = []
        for code_file in knowledge.files:
            for imp in code_file.imports:
                if resolver.is_standard_library(imp):
                    continue
                target = resolver.resolve(code_file.relative_path, imp)
                if target is None:
                    unresolved.append(
                        UnresolvedImport(
                            file_path=code_file.relative_path, statement=imp
                        )
                    )
                elif target != code_file.relative_path:
                    graph.add_edge(code_file.relative_path, target)

        repository_graph = RepositoryGraph(graph, unresolved)
        logger.info(
            "Dependency graph built: %d nodes, %d edges, %d unresolved imports",
            repository_graph.node_count,
            repository_graph.edge_count,
            len(unresolved),
        )
        return repository_graph

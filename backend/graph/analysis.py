"""Read-only analysis of a repository dependency graph.

Consumes a RepositoryGraph and produces summary metrics. Never mutates the
graph and performs no visualization.
"""

import logging

import networkx as nx
from pydantic import BaseModel

from graph.models import RepositoryGraph

logger = logging.getLogger(__name__)


class RepositoryGraphAnalysis(BaseModel):
    """Structural metrics for one repository dependency graph.

    Node-role definitions (mutually exclusive where it matters):

    - root modules: no incoming edges but at least one outgoing edge
      (entry points nothing else imports)
    - leaf modules: no outgoing edges but at least one incoming edge
      (pure dependencies importing nothing themselves)
    - isolated files: no edges at all (isolated files are *not* listed as
      roots or leaves)
    """

    node_count: int
    edge_count: int
    density: float
    cycles: list[list[str]]
    fan_in: dict[str, int]
    fan_out: dict[str, int]
    root_modules: list[str]
    leaf_modules: list[str]
    isolated_files: list[str]
    connected_components: list[list[str]]
    largest_component_size: int
    average_fan_in: float
    average_fan_out: float

    @property
    def cycle_count(self) -> int:
        """Number of circular dependencies."""
        return len(self.cycles)

    @property
    def component_count(self) -> int:
        """Number of weakly connected components."""
        return len(self.connected_components)

    @property
    def has_cycles(self) -> bool:
        """True when the graph contains at least one cycle."""
        return bool(self.cycles)

    def get_most_imported_files(self, limit: int = 10) -> list[tuple[str, int]]:
        """Files with the highest fan-in, as (path, count) pairs."""
        return self._top(self.fan_in, limit)

    def get_most_dependent_files(self, limit: int = 10) -> list[tuple[str, int]]:
        """Files with the highest fan-out, as (path, count) pairs."""
        return self._top(self.fan_out, limit)

    @staticmethod
    def _top(counts: dict[str, int], limit: int) -> list[tuple[str, int]]:
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [(path, count) for path, count in ranked[:limit] if count > 0]


def analyze_graph(repository_graph: RepositoryGraph) -> RepositoryGraphAnalysis:
    """Compute a RepositoryGraphAnalysis from a RepositoryGraph."""
    graph: nx.DiGraph = repository_graph.graph
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()

    fan_in = {node: degree for node, degree in graph.in_degree()}
    fan_out = {node: degree for node, degree in graph.out_degree()}

    root_modules = sorted(
        node for node in graph if fan_in[node] == 0 and fan_out[node] > 0
    )
    leaf_modules = sorted(
        node for node in graph if fan_out[node] == 0 and fan_in[node] > 0
    )
    isolated_files = sorted(
        node for node in graph if fan_in[node] == 0 and fan_out[node] == 0
    )

    cycles = sorted(
        (_normalize_cycle(cycle) for cycle in nx.simple_cycles(graph)),
        key=lambda cycle: (len(cycle), cycle),
    )

    components = sorted(
        (sorted(component) for component in nx.weakly_connected_components(graph)),
        key=lambda component: (-len(component), component),
    )

    analysis = RepositoryGraphAnalysis(
        node_count=node_count,
        edge_count=edge_count,
        density=nx.density(graph),
        cycles=cycles,
        fan_in=fan_in,
        fan_out=fan_out,
        root_modules=root_modules,
        leaf_modules=leaf_modules,
        isolated_files=isolated_files,
        connected_components=components,
        largest_component_size=len(components[0]) if components else 0,
        average_fan_in=edge_count / node_count if node_count else 0.0,
        average_fan_out=edge_count / node_count if node_count else 0.0,
    )
    logger.info(
        "Graph analysis: %d nodes, %d edges, %d cycles, %d components",
        node_count,
        edge_count,
        analysis.cycle_count,
        analysis.component_count,
    )
    return analysis


def _normalize_cycle(cycle: list[str]) -> list[str]:
    """Rotate a cycle so it starts at its smallest node (deterministic)."""
    pivot = cycle.index(min(cycle))
    return cycle[pivot:] + cycle[:pivot]

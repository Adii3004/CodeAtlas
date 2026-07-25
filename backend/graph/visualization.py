"""Visualization-friendly model of the repository dependency graph.

Transforms a RepositoryGraph into flat, serializable node/edge lists with
deterministic initial positions. No rendering happens here — this is the
payload a frontend will consume later.
"""

import logging
from pathlib import PurePosixPath

import networkx as nx
from pydantic import BaseModel, PrivateAttr

from graph.models import RepositoryGraph
from scanner.classifier import FileCategory
from scanner.language import ProgrammingLanguage

logger = logging.getLogger(__name__)

DEFAULT_WIDTH = 1000.0
DEFAULT_HEIGHT = 1000.0
DEFAULT_SEED = 42

#: Group name used for files that live directly in the repository root.
ROOT_GROUP = "."


class GraphNode(BaseModel):
    """One file, ready to draw."""

    id: str
    label: str
    relative_path: str
    category: FileCategory
    language: ProgrammingLanguage
    symbol_count: int
    import_count: int
    fan_in: int
    fan_out: int
    group: str
    x: float
    y: float


class GraphEdge(BaseModel):
    """One dependency, pointing from importer to imported."""

    source: str
    target: str


class GraphVisualization(BaseModel):
    """Nodes and edges of one repository graph in draw-ready form."""

    width: float
    height: float
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    _nodes_by_id: dict[str, GraphNode] = PrivateAttr(default_factory=dict)
    _neighbor_ids: dict[str, set[str]] = PrivateAttr(default_factory=dict)

    def model_post_init(self, context: object) -> None:
        """Build the private lookup indexes after validation."""
        self._nodes_by_id = {node.id: node for node in self.nodes}
        self._neighbor_ids = {node.id: set() for node in self.nodes}
        for edge in self.edges:
            self._neighbor_ids[edge.source].add(edge.target)
            self._neighbor_ids[edge.target].add(edge.source)

    def get_node(self, node_id: str) -> GraphNode | None:
        """Look up one node by id."""
        return self._nodes_by_id.get(node_id)

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        """All nodes connected to ``node_id``, in either direction."""
        return [
            self._nodes_by_id[neighbor]
            for neighbor in sorted(self._neighbor_ids.get(node_id, ()))
        ]


def build_visualization(
    repository_graph: RepositoryGraph,
    *,
    width: float = DEFAULT_WIDTH,
    height: float = DEFAULT_HEIGHT,
    seed: int = DEFAULT_SEED,
) -> GraphVisualization:
    """Build a GraphVisualization with deterministic initial positions.

    Positions come from NetworkX ``spring_layout`` with a fixed seed and are
    scaled from its [-1, 1] range into [0, width] x [0, height].
    """
    graph: nx.DiGraph = repository_graph.graph
    positions = nx.spring_layout(graph, seed=seed) if graph else {}

    nodes: list[GraphNode] = []
    for node_id in sorted(graph.nodes):
        code_file = repository_graph.get_code_file(node_id)
        assert code_file is not None  # every node carries its CodeFile
        x, y = positions[node_id]
        parent = PurePosixPath(node_id).parent.as_posix()
        nodes.append(
            GraphNode(
                id=node_id,
                label=code_file.metadata.filename,
                relative_path=node_id,
                category=code_file.category,
                language=code_file.language,
                symbol_count=len(code_file.symbols),
                import_count=len(code_file.imports),
                fan_in=graph.in_degree(node_id),
                fan_out=graph.out_degree(node_id),
                group=parent if parent else ROOT_GROUP,
                x=round(_scale(x, width), 2),
                y=round(_scale(y, height), 2),
            )
        )

    edges = [
        GraphEdge(source=source, target=target)
        for source, target in sorted(graph.edges)
    ]

    visualization = GraphVisualization(
        width=width, height=height, nodes=nodes, edges=edges
    )
    logger.info(
        "Visualization built: %d nodes, %d edges (%gx%g)",
        len(nodes),
        len(edges),
        width,
        height,
    )
    return visualization


def _scale(value: float, extent: float) -> float:
    """Map a spring_layout coordinate from [-1, 1] into [0, extent]."""
    return (value + 1.0) / 2.0 * extent

"""Repository dependency graph model.

Wraps a NetworkX DiGraph whose nodes are repository files (keyed by
relative path, each carrying its CodeFile) and whose edges point from an
importing file to the file it imports.
"""

import networkx as nx
from pydantic import BaseModel

from knowledge.models import CodeFile
from parsers.imports import Import

#: Node attribute under which each node's CodeFile is stored.
CODE_FILE_ATTR = "code_file"


class UnresolvedImport(BaseModel):
    """An import that could not be mapped to a repository file.

    Standard-library imports are excluded; third-party packages currently
    land here (future diagnostics may classify them further).
    """

    file_path: str
    statement: Import


class RepositoryGraph:
    """The dependency graph of one repository."""

    def __init__(
        self,
        graph: nx.DiGraph,
        unresolved_imports: list[UnresolvedImport],
    ) -> None:
        self.graph = graph
        self.unresolved_imports = unresolved_imports

    @property
    def node_count(self) -> int:
        """Number of files in the graph."""
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Number of resolved dependency edges."""
        return self.graph.number_of_edges()

    def has_node(self, file: CodeFile | str) -> bool:
        """True if the file is a node in the graph."""
        return self.graph.has_node(self._key(file))

    def get_dependencies(self, file: CodeFile | str) -> list[CodeFile]:
        """Files that ``file`` imports (outgoing edges)."""
        key = self._key(file)
        if not self.graph.has_node(key):
            return []
        return [
            self._code_file(target) for target in sorted(self.graph.successors(key))
        ]

    def get_dependents(self, file: CodeFile | str) -> list[CodeFile]:
        """Files that import ``file`` (incoming edges)."""
        key = self._key(file)
        if not self.graph.has_node(key):
            return []
        return [
            self._code_file(source) for source in sorted(self.graph.predecessors(key))
        ]

    def get_code_file(self, file: CodeFile | str) -> CodeFile | None:
        """Return the CodeFile stored on a node, if present."""
        key = self._key(file)
        if not self.graph.has_node(key):
            return None
        return self._code_file(key)

    @staticmethod
    def _key(file: CodeFile | str) -> str:
        return file.relative_path if isinstance(file, CodeFile) else file

    def _code_file(self, key: str) -> CodeFile:
        return self.graph.nodes[key][CODE_FILE_ATTR]

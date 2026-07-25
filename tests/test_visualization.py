"""Unit tests for the graph visualization model."""

from pathlib import Path

import pytest

from graph import DependencyGraphBuilder, GraphVisualization, build_visualization
from knowledge import build_repository_knowledge
from scanner import FileCategory, ProgrammingLanguage, RepositoryScanner


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _visualize(root: Path, **kwargs: float | int) -> GraphVisualization:
    knowledge = build_repository_knowledge(RepositoryScanner().scan(root))
    return build_visualization(DependencyGraphBuilder().build(knowledge), **kwargs)


class TestEmptyGraph:
    def test_empty_repository(self, tmp_path: Path) -> None:
        viz = _visualize(tmp_path)

        assert viz.nodes == []
        assert viz.edges == []
        assert viz.get_node("anything.py") is None
        assert viz.get_neighbors("anything.py") == []


class TestSimpleGraph:
    @pytest.fixture
    def viz(self, tmp_path: Path) -> GraphVisualization:
        _write(tmp_path, "models.py", "M = 1\n")
        _write(tmp_path, "app.py", "import models\n")
        return _visualize(tmp_path)

    def test_nodes_and_edges(self, viz: GraphVisualization) -> None:
        assert [n.id for n in viz.nodes] == ["app.py", "models.py"]
        assert [(e.source, e.target) for e in viz.edges] == [("app.py", "models.py")]

    def test_get_node(self, viz: GraphVisualization) -> None:
        node = viz.get_node("app.py")
        assert node is not None
        assert node.label == "app.py"
        assert viz.get_node("missing.py") is None

    def test_get_neighbors_both_directions(self, viz: GraphVisualization) -> None:
        # Neighbors work in either edge direction.
        assert [n.id for n in viz.get_neighbors("app.py")] == ["models.py"]
        assert [n.id for n in viz.get_neighbors("models.py")] == ["app.py"]

    def test_positions_within_bounds(self, viz: GraphVisualization) -> None:
        assert viz.width == 1000.0
        assert viz.height == 1000.0
        for node in viz.nodes:
            assert 0.0 <= node.x <= viz.width
            assert 0.0 <= node.y <= viz.height


class TestDeterministicLayout:
    def test_same_seed_same_positions(self, tmp_path: Path) -> None:
        for name in ("a.py", "b.py", "c.py"):
            _write(tmp_path, name, "x = 1\n")
        _write(tmp_path, "hub.py", "import a\nimport b\nimport c\n")

        first = _visualize(tmp_path)
        second = _visualize(tmp_path)

        assert [(n.id, n.x, n.y) for n in first.nodes] == [
            (n.id, n.x, n.y) for n in second.nodes
        ]

    def test_different_seed_different_positions(self, tmp_path: Path) -> None:
        for name in ("a.py", "b.py", "c.py"):
            _write(tmp_path, name, "x = 1\n")
        _write(tmp_path, "hub.py", "import a\nimport b\nimport c\n")

        default = _visualize(tmp_path)
        reseeded = _visualize(tmp_path, seed=7)

        assert [(n.x, n.y) for n in default.nodes] != [
            (n.x, n.y) for n in reseeded.nodes
        ]

    def test_custom_dimensions_scale_positions(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.py", "import b\n")
        _write(tmp_path, "b.py", "x = 1\n")

        viz = _visualize(tmp_path, width=200.0, height=100.0)

        assert viz.width == 200.0
        for node in viz.nodes:
            assert 0.0 <= node.x <= 200.0
            assert 0.0 <= node.y <= 100.0


class TestNodeMetadata:
    def test_metadata_fields(self, tmp_path: Path) -> None:
        _write(tmp_path, "pkg/__init__.py")
        _write(
            tmp_path,
            "pkg/service.py",
            "import os\nfrom . import helpers\n\nclass Service:\n    pass\n\n"
            "def run():\n    pass\n",
        )
        _write(tmp_path, "pkg/helpers.py", "H = 1\n")

        viz = _visualize(tmp_path)

        node = viz.get_node("pkg/service.py")
        assert node is not None
        assert node.label == "service.py"
        assert node.relative_path == "pkg/service.py"
        assert node.category is FileCategory.SOURCE_CODE
        assert node.language is ProgrammingLanguage.PYTHON
        assert node.symbol_count == 2  # Service, run
        assert node.import_count == 2  # os + relative helpers
        assert node.fan_in == 0
        assert node.fan_out == 1  # only helpers resolves in-repo
        assert node.group == "pkg"

    def test_root_file_group(self, tmp_path: Path) -> None:
        _write(tmp_path, "main.py", "x = 1\n")

        viz = _visualize(tmp_path)

        assert viz.get_node("main.py").group == "."

    def test_non_python_node_metadata(self, tmp_path: Path) -> None:
        _write(tmp_path, "README.md", "# docs\n")

        viz = _visualize(tmp_path)

        node = viz.get_node("README.md")
        assert node is not None
        assert node.category is FileCategory.DOCUMENTATION
        assert node.language is ProgrammingLanguage.MARKDOWN
        assert node.symbol_count == 0
        assert node.fan_in == 0


class TestEdgeGeneration:
    def test_edges_match_graph(self, tmp_path: Path) -> None:
        _write(tmp_path, "core.py", "C = 1\n")
        _write(tmp_path, "user1.py", "import core\n")
        _write(tmp_path, "user2.py", "import core\n")

        viz = _visualize(tmp_path)

        assert [(e.source, e.target) for e in viz.edges] == [
            ("user1.py", "core.py"),
            ("user2.py", "core.py"),
        ]

    def test_fan_counts_match_edges(self, tmp_path: Path) -> None:
        _write(tmp_path, "core.py", "C = 1\n")
        _write(tmp_path, "user1.py", "import core\n")
        _write(tmp_path, "user2.py", "import core\n")

        viz = _visualize(tmp_path)

        assert viz.get_node("core.py").fan_in == 2
        assert viz.get_node("core.py").fan_out == 0
        assert [n.id for n in viz.get_neighbors("core.py")] == [
            "user1.py",
            "user2.py",
        ]

    def test_serialization(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.py", "import b\n")
        _write(tmp_path, "b.py", "x = 1\n")

        viz = _visualize(tmp_path)
        restored = GraphVisualization.model_validate_json(viz.model_dump_json())

        assert [n.id for n in restored.nodes] == ["a.py", "b.py"]
        # Helpers work after deserialization too (private indexes rebuilt).
        assert restored.get_node("a.py") is not None
        assert [n.id for n in restored.get_neighbors("b.py")] == ["a.py"]

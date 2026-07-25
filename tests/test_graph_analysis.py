"""Unit tests for repository graph analysis."""

from pathlib import Path

import pytest

from graph import DependencyGraphBuilder, RepositoryGraphAnalysis, analyze_graph
from knowledge import build_repository_knowledge
from scanner import RepositoryScanner


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _analyze(root: Path) -> RepositoryGraphAnalysis:
    knowledge = build_repository_knowledge(RepositoryScanner().scan(root))
    return analyze_graph(DependencyGraphBuilder().build(knowledge))


class TestSimpleGraph:
    """Chain: app.py -> service.py -> models.py"""

    @pytest.fixture
    def analysis(self, tmp_path: Path) -> RepositoryGraphAnalysis:
        _write(tmp_path, "models.py", "M = 1\n")
        _write(tmp_path, "service.py", "import models\n")
        _write(tmp_path, "app.py", "import service\n")
        return _analyze(tmp_path)

    def test_counts(self, analysis: RepositoryGraphAnalysis) -> None:
        assert analysis.node_count == 3
        assert analysis.edge_count == 2
        assert analysis.cycles == []
        assert not analysis.has_cycles

    def test_fan_in_and_out(self, analysis: RepositoryGraphAnalysis) -> None:
        assert analysis.fan_in == {"app.py": 0, "service.py": 1, "models.py": 1}
        assert analysis.fan_out == {"app.py": 1, "service.py": 1, "models.py": 0}

    def test_roots_and_leaves(self, analysis: RepositoryGraphAnalysis) -> None:
        assert analysis.root_modules == ["app.py"]
        assert analysis.leaf_modules == ["models.py"]
        assert analysis.isolated_files == []

    def test_components_and_density(self, analysis: RepositoryGraphAnalysis) -> None:
        assert analysis.component_count == 1
        assert analysis.largest_component_size == 3
        assert analysis.connected_components[0] == [
            "app.py",
            "models.py",
            "service.py",
        ]
        # DiGraph density: edges / (n * (n - 1)) = 2 / 6
        assert analysis.density == pytest.approx(2 / 6)
        assert analysis.average_fan_out == pytest.approx(2 / 3)

    def test_helper_rankings(self, analysis: RepositoryGraphAnalysis) -> None:
        assert analysis.get_most_imported_files() == [
            ("models.py", 1),
            ("service.py", 1),
        ]
        assert analysis.get_most_dependent_files(limit=1) == [("app.py", 1)]


class TestCycles:
    def test_two_file_cycle(self, tmp_path: Path) -> None:
        _write(tmp_path, "alpha.py", "import beta\n")
        _write(tmp_path, "beta.py", "import alpha\n")

        analysis = _analyze(tmp_path)

        assert analysis.has_cycles
        assert analysis.cycles == [["alpha.py", "beta.py"]]
        assert analysis.cycle_count == 1

    def test_three_file_cycle_plus_outsider(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.py", "import b\n")
        _write(tmp_path, "b.py", "import c\n")
        _write(tmp_path, "c.py", "import a\n")
        _write(tmp_path, "outsider.py", "import a\n")

        analysis = _analyze(tmp_path)

        assert analysis.cycles == [["a.py", "b.py", "c.py"]]
        # The cycle members are neither roots nor leaves; outsider is a root.
        assert analysis.root_modules == ["outsider.py"]
        assert analysis.leaf_modules == []

    def test_self_cycles_are_impossible(self, tmp_path: Path) -> None:
        # The builder skips self-imports, so a module importing its own
        # name yields no self-loop cycle.
        _write(tmp_path, "selfish.py", "import selfish\n")

        analysis = _analyze(tmp_path)

        assert analysis.cycles == []


class TestIsolatedFiles:
    def test_isolated_python_and_non_python(self, tmp_path: Path) -> None:
        _write(tmp_path, "core.py", "X = 1\n")
        _write(tmp_path, "user.py", "import core\n")
        _write(tmp_path, "loner.py", "Y = 2\n")
        _write(tmp_path, "README.md", "# docs\n")

        analysis = _analyze(tmp_path)

        assert analysis.isolated_files == ["README.md", "loner.py"]
        # Isolated files are excluded from roots and leaves.
        assert analysis.root_modules == ["user.py"]
        assert analysis.leaf_modules == ["core.py"]

    def test_isolated_files_are_singleton_components(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.py", "import b\n")
        _write(tmp_path, "b.py", "B = 1\n")
        _write(tmp_path, "solo.py", "S = 1\n")

        analysis = _analyze(tmp_path)

        assert analysis.component_count == 2
        assert analysis.connected_components == [["a.py", "b.py"], ["solo.py"]]


class TestDisconnectedRepositories:
    def test_two_clusters(self, tmp_path: Path) -> None:
        _write(tmp_path, "app1/__init__.py")
        _write(tmp_path, "app1/main.py", "from . import util\n")
        _write(tmp_path, "app1/util.py", "U = 1\n")
        _write(tmp_path, "app2/__init__.py")
        _write(tmp_path, "app2/main.py", "from . import helper\n")
        _write(tmp_path, "app2/helper.py", "H = 1\n")

        analysis = _analyze(tmp_path)

        # Two 2-node clusters plus two isolated __init__.py singletons.
        assert analysis.component_count == 4
        sizes = [len(c) for c in analysis.connected_components]
        assert sizes == [2, 2, 1, 1]
        assert analysis.largest_component_size == 2

    def test_components_sorted_by_size_then_name(self, tmp_path: Path) -> None:
        _write(tmp_path, "big1.py", "import big2\nimport big3\n")
        _write(tmp_path, "big2.py", "B = 2\n")
        _write(tmp_path, "big3.py", "B = 3\n")
        _write(tmp_path, "small1.py", "import small2\n")
        _write(tmp_path, "small2.py", "S = 2\n")

        analysis = _analyze(tmp_path)

        assert [len(c) for c in analysis.connected_components] == [3, 2]
        assert analysis.largest_component_size == 3


class TestEmptyRepository:
    def test_empty_repository(self, tmp_path: Path) -> None:
        analysis = _analyze(tmp_path)

        assert analysis.node_count == 0
        assert analysis.edge_count == 0
        assert analysis.density == 0.0
        assert analysis.cycles == []
        assert analysis.fan_in == {}
        assert analysis.fan_out == {}
        assert analysis.root_modules == []
        assert analysis.leaf_modules == []
        assert analysis.isolated_files == []
        assert analysis.connected_components == []
        assert analysis.largest_component_size == 0
        assert analysis.average_fan_in == 0.0
        assert analysis.get_most_imported_files() == []
        assert analysis.get_most_dependent_files() == []

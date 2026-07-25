"""Unit tests for the repository dependency graph."""

from pathlib import Path

from graph import DependencyGraphBuilder, RepositoryGraph
from knowledge import build_repository_knowledge
from scanner import RepositoryScanner


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _build(root: Path) -> RepositoryGraph:
    knowledge = build_repository_knowledge(RepositoryScanner().scan(root))
    return DependencyGraphBuilder().build(knowledge)


class TestSimpleDependency:
    def test_single_edge(self, tmp_path: Path) -> None:
        _write(tmp_path, "b.py", "VALUE = 1\n")
        _write(tmp_path, "a.py", "import b\n")

        graph = _build(tmp_path)

        assert graph.node_count == 2
        assert graph.edge_count == 1
        assert [f.relative_path for f in graph.get_dependencies("a.py")] == ["b.py"]
        assert [f.relative_path for f in graph.get_dependents("b.py")] == ["a.py"]

    def test_from_import(self, tmp_path: Path) -> None:
        _write(tmp_path, "helpers.py", "def helper():\n    pass\n")
        _write(tmp_path, "main.py", "from helpers import helper\n")

        graph = _build(tmp_path)

        assert [f.relative_path for f in graph.get_dependencies("main.py")] == [
            "helpers.py"
        ]

    def test_nodes_reference_code_files(self, tmp_path: Path) -> None:
        _write(tmp_path, "solo.py", "class Solo:\n    pass\n")

        graph = _build(tmp_path)

        code_file = graph.get_code_file("solo.py")
        assert code_file is not None
        assert code_file.symbols[0].name == "Solo"
        # Helpers accept the CodeFile object as well as the path string.
        assert graph.has_node(code_file)
        assert graph.get_dependencies(code_file) == []


class TestMultipleImports:
    def test_fan_out(self, tmp_path: Path) -> None:
        _write(tmp_path, "one.py", "X = 1\n")
        _write(tmp_path, "two.py", "Y = 2\n")
        _write(tmp_path, "three.py", "Z = 3\n")
        _write(tmp_path, "hub.py", "import one\nimport two\nimport three\n")

        graph = _build(tmp_path)

        deps = [f.relative_path for f in graph.get_dependencies("hub.py")]
        assert deps == ["one.py", "three.py", "two.py"]  # sorted
        assert graph.edge_count == 3

    def test_fan_in(self, tmp_path: Path) -> None:
        _write(tmp_path, "core.py", "SHARED = True\n")
        _write(tmp_path, "user1.py", "import core\n")
        _write(tmp_path, "user2.py", "from core import SHARED\n")

        graph = _build(tmp_path)

        dependents = [f.relative_path for f in graph.get_dependents("core.py")]
        assert dependents == ["user1.py", "user2.py"]

    def test_duplicate_imports_create_one_edge(self, tmp_path: Path) -> None:
        _write(tmp_path, "target.py", "A = 1\nB = 2\n")
        _write(tmp_path, "source.py", "from target import A\nfrom target import B\n")

        graph = _build(tmp_path)

        assert graph.edge_count == 1


class TestRelativeImports:
    def test_same_package_relative(self, tmp_path: Path) -> None:
        _write(tmp_path, "pkg/__init__.py")
        _write(tmp_path, "pkg/models.py", "M = 1\n")
        _write(tmp_path, "pkg/service.py", "from .models import M\n")

        graph = _build(tmp_path)

        assert [f.relative_path for f in graph.get_dependencies("pkg/service.py")] == [
            "pkg/models.py"
        ]

    def test_from_dot_import_module(self, tmp_path: Path) -> None:
        _write(tmp_path, "pkg/__init__.py")
        _write(tmp_path, "pkg/models.py", "M = 1\n")
        _write(tmp_path, "pkg/api.py", "from . import models\n")

        graph = _build(tmp_path)

        assert [f.relative_path for f in graph.get_dependencies("pkg/api.py")] == [
            "pkg/models.py"
        ]

    def test_parent_package_relative(self, tmp_path: Path) -> None:
        _write(tmp_path, "app/__init__.py")
        _write(tmp_path, "app/config.py", "C = 1\n")
        _write(tmp_path, "app/sub/__init__.py")
        _write(tmp_path, "app/sub/worker.py", "from ..config import C\n")

        graph = _build(tmp_path)

        assert [
            f.relative_path for f in graph.get_dependencies("app/sub/worker.py")
        ] == ["app/config.py"]

    def test_relative_import_of_package_itself(self, tmp_path: Path) -> None:
        _write(tmp_path, "pkg/__init__.py", "NAME = 'pkg'\n")
        _write(tmp_path, "pkg/user.py", "from . import NAME\n")

        graph = _build(tmp_path)

        # `from . import NAME` where NAME is not a module resolves to the
        # package __init__.
        assert [f.relative_path for f in graph.get_dependencies("pkg/user.py")] == [
            "pkg/__init__.py"
        ]


class TestUnresolvedImports:
    def test_third_party_is_unresolved_not_an_edge(self, tmp_path: Path) -> None:
        _write(tmp_path, "app.py", "import numpy\nfrom requests import get\n")

        graph = _build(tmp_path)

        assert graph.edge_count == 0
        modules = [u.statement.module for u in graph.unresolved_imports]
        assert modules == ["numpy", "requests"]
        assert all(u.file_path == "app.py" for u in graph.unresolved_imports)

    def test_stdlib_is_ignored_entirely(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "app.py",
            "import os\nimport sys\nfrom pathlib import Path\n"
            "from __future__ import annotations\n",
        )

        graph = _build(tmp_path)

        assert graph.edge_count == 0
        assert graph.unresolved_imports == []

    def test_broken_local_import_is_unresolved(self, tmp_path: Path) -> None:
        _write(tmp_path, "app.py", "from missing_module import thing\n")

        graph = _build(tmp_path)

        [unresolved] = graph.unresolved_imports
        assert unresolved.statement.module == "missing_module"


class TestEmptyRepository:
    def test_empty_repository(self, tmp_path: Path) -> None:
        graph = _build(tmp_path)

        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert graph.unresolved_imports == []
        assert not graph.has_node("anything.py")
        assert graph.get_dependencies("anything.py") == []
        assert graph.get_dependents("anything.py") == []


class TestNonPythonNodes:
    def test_every_file_is_a_node(self, tmp_path: Path) -> None:
        _write(tmp_path, "main.py", "x = 1\n")
        _write(tmp_path, "README.md", "# readme\n")
        _write(tmp_path, "data.json", "{}\n")

        graph = _build(tmp_path)

        assert graph.node_count == 3
        assert graph.has_node("README.md")
        assert graph.edge_count == 0

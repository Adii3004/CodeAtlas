"""Unit tests for the repository report generator."""

import json
from pathlib import Path

import pytest

from graph import DependencyGraphBuilder, analyze_graph
from knowledge import build_repository_knowledge
from reports import ReportThresholds, RepositoryReport, generate_report
from scanner import RepositoryScanner


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _report(root: Path, thresholds: ReportThresholds | None = None) -> RepositoryReport:
    knowledge = build_repository_knowledge(RepositoryScanner().scan(root))
    graph = DependencyGraphBuilder().build(knowledge)
    analysis = analyze_graph(graph)
    return generate_report(knowledge, graph, analysis, thresholds)


class TestEmptyRepository:
    def test_empty_report(self, tmp_path: Path) -> None:
        report = _report(tmp_path)

        assert report.general.total_files == 0
        assert report.general.parsed_files == 0
        assert report.general.total_symbols == 0
        assert report.languages == {}
        assert report.graph_summary.nodes == 0
        assert report.issues.issue_count == 0

    def test_empty_markdown_and_json(self, tmp_path: Path) -> None:
        report = _report(tmp_path)

        markdown = report.to_markdown()
        assert "# Repository Report:" in markdown
        assert "No issues detected." in markdown

        payload = json.loads(report.to_json())
        assert payload["general"]["total_files"] == 0


class TestSimpleRepository:
    @pytest.fixture
    def report(self, tmp_path: Path) -> RepositoryReport:
        _write(tmp_path, "models.py", "class Model:\n    pass\n")
        _write(
            tmp_path,
            "app.py",
            "import os\nimport models\n\ndef main():\n    pass\n",
        )
        _write(tmp_path, "README.md", "# readme\n")
        return _report(tmp_path)

    def test_general_section(self, report: RepositoryReport) -> None:
        assert report.general.total_files == 3
        assert report.general.parsed_files == 2
        assert report.general.total_symbols == 2  # Model, main
        assert report.general.total_imports == 2  # os, models

    def test_distributions(self, report: RepositoryReport) -> None:
        languages = {lang.value: n for lang, n in report.languages.items()}
        assert languages == {"python": 2, "markdown": 1}
        categories = {cat.value: n for cat, n in report.categories.items() if n}
        assert categories == {"source_code": 2, "documentation": 1}

    def test_graph_summary_and_architecture(self, report: RepositoryReport) -> None:
        assert report.graph_summary.nodes == 3
        assert report.graph_summary.edges == 1
        assert report.graph_summary.cycle_count == 0
        assert [r.path for r in report.architecture.most_imported] == ["models.py"]
        assert report.architecture.root_modules == ["app.py"]
        assert report.architecture.leaf_modules == ["models.py"]
        assert report.architecture.isolated_files == ["README.md"]

    def test_markdown_contains_sections(self, report: RepositoryReport) -> None:
        markdown = report.to_markdown()
        for heading in (
            "## General",
            "## Languages",
            "## Categories",
            "## Dependency Graph",
            "## Architecture Highlights",
            "## Potential Issues",
        ):
            assert heading in markdown
        assert "| Total files | 3 |" in markdown
        assert "`models.py` (1)" in markdown

    def test_json_round_trip(self, report: RepositoryReport) -> None:
        restored = RepositoryReport.model_validate_json(report.to_json())
        assert restored.general.total_files == 3
        assert restored.architecture.root_modules == ["app.py"]


class TestCyclicRepository:
    @pytest.fixture
    def report(self, tmp_path: Path) -> RepositoryReport:
        _write(tmp_path, "alpha.py", "import beta\n")
        _write(tmp_path, "beta.py", "import alpha\n")
        return _report(tmp_path)

    def test_cycle_reported_as_issue(self, report: RepositoryReport) -> None:
        assert report.graph_summary.cycle_count == 1
        assert report.issues.circular_dependencies == [["alpha.py", "beta.py"]]
        assert report.issues.issue_count == 1

    def test_cycle_in_markdown(self, report: RepositoryReport) -> None:
        markdown = report.to_markdown()
        assert "### Circular dependencies" in markdown
        assert "- alpha.py -> beta.py -> alpha.py" in markdown
        assert "No issues detected." not in markdown


class TestUnresolvedImports:
    def test_unresolved_reported(self, tmp_path: Path) -> None:
        _write(tmp_path, "app.py", "import numpy\nfrom flask import Flask\n")

        report = _report(tmp_path)

        modules = [u.statement.module for u in report.issues.unresolved_imports]
        assert modules == ["numpy", "flask"]
        markdown = report.to_markdown()
        assert "### Unresolved imports" in markdown
        assert "`app.py` line 1: `numpy`" in markdown
        assert "`app.py` line 2: `flask.Flask`" in markdown

    def test_stdlib_not_reported(self, tmp_path: Path) -> None:
        _write(tmp_path, "app.py", "import os\nimport sys\n")

        report = _report(tmp_path)

        assert report.issues.unresolved_imports == []
        assert report.issues.issue_count == 0


class TestThresholds:
    def test_default_thresholds_do_not_flag_small_fan(self, tmp_path: Path) -> None:
        _write(tmp_path, "core.py", "C = 1\n")
        _write(tmp_path, "u1.py", "import core\n")
        _write(tmp_path, "u2.py", "import core\n")

        report = _report(tmp_path)  # default threshold: 10

        assert report.issues.high_fan_in == []

    def test_custom_thresholds_flag_fan_in_and_out(self, tmp_path: Path) -> None:
        _write(tmp_path, "core.py", "C = 1\n")
        _write(tmp_path, "u1.py", "import core\n")
        _write(tmp_path, "u2.py", "import core\nimport u1\n")

        thresholds = ReportThresholds(high_fan_in=2, high_fan_out=2)
        report = _report(tmp_path, thresholds)

        assert [(r.path, r.count) for r in report.issues.high_fan_in] == [
            ("core.py", 2)
        ]
        assert [(r.path, r.count) for r in report.issues.high_fan_out] == [("u2.py", 2)]

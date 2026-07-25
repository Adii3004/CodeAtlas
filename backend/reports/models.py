"""Report models: a structured, exportable repository engineering report."""

from datetime import datetime

from pydantic import BaseModel

from graph.models import UnresolvedImport
from scanner.classifier import FileCategory
from scanner.language import ProgrammingLanguage


class RankedFile(BaseModel):
    """A file with an associated count (fan-in, fan-out, ...)."""

    path: str
    count: int


class GeneralSection(BaseModel):
    repository_name: str
    root_path: str
    generated_at: datetime
    total_files: int
    parsed_files: int
    total_symbols: int
    total_imports: int


class GraphSummarySection(BaseModel):
    nodes: int
    edges: int
    density: float
    connected_components: int
    largest_component_size: int
    cycle_count: int


class ArchitectureSection(BaseModel):
    most_imported: list[RankedFile]
    most_dependent: list[RankedFile]
    root_modules: list[str]
    leaf_modules: list[str]
    isolated_files: list[str]


class IssuesSection(BaseModel):
    circular_dependencies: list[list[str]]
    high_fan_in: list[RankedFile]
    high_fan_out: list[RankedFile]
    unresolved_imports: list[UnresolvedImport]

    @property
    def issue_count(self) -> int:
        """Total number of flagged issues."""
        return (
            len(self.circular_dependencies)
            + len(self.high_fan_in)
            + len(self.high_fan_out)
            + len(self.unresolved_imports)
        )


class RepositoryReport(BaseModel):
    """Complete engineering report for one repository."""

    general: GeneralSection
    languages: dict[ProgrammingLanguage, int]
    categories: dict[FileCategory, int]
    graph_summary: GraphSummarySection
    architecture: ArchitectureSection
    issues: IssuesSection

    def to_json(self, *, indent: int = 2) -> str:
        """Export the report as pretty-printed JSON."""
        return self.model_dump_json(indent=indent)

    def to_markdown(self) -> str:
        """Export the report as a Markdown document."""
        lines: list[str] = []
        general = self.general
        lines.append(f"# Repository Report: {general.repository_name}")
        lines.append("")
        lines.append(f"Generated: {general.generated_at:%Y-%m-%d %H:%M:%S}")
        lines.append(f"Root: `{general.root_path}`")
        lines.append("")

        lines.append("## General")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| Total files | {general.total_files} |")
        lines.append(f"| Parsed files | {general.parsed_files} |")
        lines.append(f"| Total symbols | {general.total_symbols} |")
        lines.append(f"| Total imports | {general.total_imports} |")
        lines.append("")

        lines.append("## Languages")
        lines.append("")
        lines.extend(
            self._count_table(
                {lang.value: count for lang, count in self.languages.items()}
            )
        )
        lines.append("")

        lines.append("## Categories")
        lines.append("")
        lines.extend(
            self._count_table(
                {cat.value: count for cat, count in self.categories.items() if count}
            )
        )
        lines.append("")

        summary = self.graph_summary
        lines.append("## Dependency Graph")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| Nodes | {summary.nodes} |")
        lines.append(f"| Edges | {summary.edges} |")
        lines.append(f"| Density | {summary.density:.4f} |")
        lines.append(f"| Connected components | {summary.connected_components} |")
        lines.append(f"| Largest component | {summary.largest_component_size} |")
        lines.append(f"| Cycles | {summary.cycle_count} |")
        lines.append("")

        arch = self.architecture
        lines.append("## Architecture Highlights")
        lines.append("")
        lines.extend(self._ranked_list("Most imported files", arch.most_imported))
        lines.extend(self._ranked_list("Most dependent files", arch.most_dependent))
        lines.extend(self._path_list("Root modules", arch.root_modules))
        lines.extend(self._path_list("Leaf modules", arch.leaf_modules))
        lines.extend(self._path_list("Isolated files", arch.isolated_files))

        issues = self.issues
        lines.append("## Potential Issues")
        lines.append("")
        if issues.issue_count == 0:
            lines.append("No issues detected.")
            lines.append("")
        else:
            if issues.circular_dependencies:
                lines.append("### Circular dependencies")
                lines.append("")
                for cycle in issues.circular_dependencies:
                    lines.append(f"- {' -> '.join(cycle)} -> {cycle[0]}")
                lines.append("")
            if issues.high_fan_in:
                lines.extend(
                    self._ranked_list("High fan-in modules", issues.high_fan_in)
                )
            if issues.high_fan_out:
                lines.extend(
                    self._ranked_list("High fan-out modules", issues.high_fan_out)
                )
            if issues.unresolved_imports:
                lines.append("### Unresolved imports")
                lines.append("")
                for unresolved in issues.unresolved_imports:
                    statement = unresolved.statement
                    target = statement.module or ""
                    if statement.name:
                        target = (
                            f"{target}.{statement.name}" if target else statement.name
                        )
                    lines.append(
                        f"- `{unresolved.file_path}` line {statement.line}: `{target}`"
                    )
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _count_table(counts: dict[str, int]) -> list[str]:
        if not counts:
            return ["(none)"]
        lines = ["| Name | Files |", "| --- | --- |"]
        lines.extend(f"| {name} | {count} |" for name, count in counts.items())
        return lines

    @staticmethod
    def _ranked_list(title: str, ranked: list[RankedFile]) -> list[str]:
        lines = [f"### {title}", ""]
        if not ranked:
            lines.append("(none)")
        else:
            lines.extend(f"- `{item.path}` ({item.count})" for item in ranked)
        lines.append("")
        return lines

    @staticmethod
    def _path_list(title: str, paths: list[str]) -> list[str]:
        lines = [f"### {title}", ""]
        if not paths:
            lines.append("(none)")
        else:
            lines.extend(f"- `{path}`" for path in paths)
        lines.append("")
        return lines

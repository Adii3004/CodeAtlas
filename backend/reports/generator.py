"""Report generator: merges knowledge, graph, and analysis into a report."""

import logging
from datetime import datetime

from pydantic import BaseModel

from graph.analysis import RepositoryGraphAnalysis
from graph.models import RepositoryGraph
from knowledge.models import RepositoryKnowledge
from reports.models import (
    ArchitectureSection,
    GeneralSection,
    GraphSummarySection,
    IssuesSection,
    RankedFile,
    RepositoryReport,
)

logger = logging.getLogger(__name__)


class ReportThresholds(BaseModel):
    """Configurable limits used when flagging potential issues."""

    high_fan_in: int = 10
    high_fan_out: int = 10
    top_files_limit: int = 10


class ReportGenerator:
    """Builds a RepositoryReport; thresholds are injectable, not hardcoded."""

    def __init__(self, thresholds: ReportThresholds | None = None) -> None:
        self.thresholds = thresholds or ReportThresholds()

    def generate(
        self,
        knowledge: RepositoryKnowledge,
        repository_graph: RepositoryGraph,
        analysis: RepositoryGraphAnalysis,
    ) -> RepositoryReport:
        """Generate the complete repository report."""
        limit = self.thresholds.top_files_limit

        report = RepositoryReport(
            general=GeneralSection(
                repository_name=knowledge.repository_name,
                root_path=knowledge.root_path,
                generated_at=datetime.now(),
                total_files=knowledge.total_files,
                parsed_files=len(knowledge.parsed_files),
                total_symbols=knowledge.total_symbols,
                total_imports=knowledge.total_imports,
            ),
            languages=knowledge.inventory.language_counts,
            categories=knowledge.inventory.category_counts,
            graph_summary=GraphSummarySection(
                nodes=analysis.node_count,
                edges=analysis.edge_count,
                density=analysis.density,
                connected_components=analysis.component_count,
                largest_component_size=analysis.largest_component_size,
                cycle_count=analysis.cycle_count,
            ),
            architecture=ArchitectureSection(
                most_imported=[
                    RankedFile(path=path, count=count)
                    for path, count in analysis.get_most_imported_files(limit)
                ],
                most_dependent=[
                    RankedFile(path=path, count=count)
                    for path, count in analysis.get_most_dependent_files(limit)
                ],
                root_modules=analysis.root_modules,
                leaf_modules=analysis.leaf_modules,
                isolated_files=analysis.isolated_files,
            ),
            issues=IssuesSection(
                circular_dependencies=analysis.cycles,
                high_fan_in=self._over_threshold(
                    analysis.fan_in, self.thresholds.high_fan_in
                ),
                high_fan_out=self._over_threshold(
                    analysis.fan_out, self.thresholds.high_fan_out
                ),
                unresolved_imports=repository_graph.unresolved_imports,
            ),
        )
        logger.info(
            "Report generated for %s: %d files, %d issues flagged",
            report.general.repository_name,
            report.general.total_files,
            report.issues.issue_count,
        )
        return report

    @staticmethod
    def _over_threshold(counts: dict[str, int], threshold: int) -> list[RankedFile]:
        """Files whose count meets or exceeds the threshold, ranked."""
        flagged = [
            (path, count) for path, count in counts.items() if count >= threshold
        ]
        flagged.sort(key=lambda item: (-item[1], item[0]))
        return [RankedFile(path=path, count=count) for path, count in flagged]


def generate_report(
    knowledge: RepositoryKnowledge,
    repository_graph: RepositoryGraph,
    analysis: RepositoryGraphAnalysis,
    thresholds: ReportThresholds | None = None,
) -> RepositoryReport:
    """Convenience wrapper around :class:`ReportGenerator`."""
    return ReportGenerator(thresholds).generate(knowledge, repository_graph, analysis)

"""Reports package: human-readable engineering reports, no AI involved."""

from reports.generator import ReportGenerator, ReportThresholds, generate_report
from reports.models import (
    ArchitectureSection,
    GeneralSection,
    GraphSummarySection,
    IssuesSection,
    RankedFile,
    RepositoryReport,
)

__all__ = [
    "ArchitectureSection",
    "GeneralSection",
    "GraphSummarySection",
    "IssuesSection",
    "RankedFile",
    "ReportGenerator",
    "ReportThresholds",
    "RepositoryReport",
    "generate_report",
]

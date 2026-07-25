"""Builder that assembles a RepositoryKnowledge from a ScanResult.

Pure coordination: the scanner scans, the parser manager parses, the
inventory summarizes — this module only merges their outputs.
"""

import logging
from datetime import datetime

from knowledge.models import CodeFile, RepositoryKnowledge
from parsers.manager import ParserManager, create_default_manager
from scanner.inventory import build_inventory
from scanner.models import FileMetadata, ScanResult

logger = logging.getLogger(__name__)


class KnowledgeBuilder:
    """Coordinates parsing and aggregation into one unified model."""

    def __init__(self, parser_manager: ParserManager | None = None) -> None:
        self._manager = parser_manager or create_default_manager()

    def build(self, scan_result: ScanResult) -> RepositoryKnowledge:
        """Merge scan, parse, and inventory data into RepositoryKnowledge."""
        inventory = build_inventory(scan_result)
        files = [self._build_code_file(meta) for meta in scan_result.files]

        knowledge = RepositoryKnowledge(
            repository_name=inventory.repository_name,
            root_path=scan_result.root_path,
            generated_at=datetime.now(),
            total_files=scan_result.total_files,
            total_size_bytes=scan_result.total_size_bytes,
            inventory=inventory,
            files=files,
        )
        logger.info(
            "Knowledge built for %s: %d files, %d parsed, %d symbols, %d imports",
            knowledge.repository_name,
            knowledge.total_files,
            len(knowledge.parsed_files),
            knowledge.total_symbols,
            knowledge.total_imports,
        )
        return knowledge

    def _build_code_file(self, metadata: FileMetadata) -> CodeFile:
        """Parse one file and merge the outcome with its metadata."""
        result = self._manager.parse(metadata)
        return CodeFile(
            metadata=metadata,
            parse_status=result.status,
            parse_message=result.message,
            error_line=result.error_line,
            error_column=result.error_column,
            symbols=result.symbols,
            imports=result.imports,
        )


def build_repository_knowledge(
    scan_result: ScanResult,
    parser_manager: ParserManager | None = None,
) -> RepositoryKnowledge:
    """Convenience wrapper around :class:`KnowledgeBuilder`."""
    return KnowledgeBuilder(parser_manager).build(scan_result)

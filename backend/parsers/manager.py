"""Parser manager: dispatches files to the parser for their language."""

import logging

from parsers.base import BaseParser
from parsers.models import ParseResult, ParseStatus
from parsers.python_parser import PythonParser
from scanner.language import ProgrammingLanguage
from scanner.models import FileMetadata

logger = logging.getLogger(__name__)


class ParserManager:
    """Registry of language parsers with graceful fallback.

    Unsupported languages never raise — they produce a ParseResult with
    status UNSUPPORTED_LANGUAGE so callers can process mixed-language
    repositories without special-casing.
    """

    def __init__(self) -> None:
        self._parsers: dict[ProgrammingLanguage, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        """Register a parser for its declared language.

        Registering a second parser for the same language replaces the
        first (logged as a warning).
        """
        if parser.language in self._parsers:
            logger.warning(
                "Replacing existing parser for %s with %s",
                parser.language,
                type(parser).__name__,
            )
        self._parsers[parser.language] = parser
        logger.info("Registered %s for %s", type(parser).__name__, parser.language)

    def get_parser(self, language: ProgrammingLanguage) -> BaseParser | None:
        """Return the registered parser for ``language``, or None."""
        return self._parsers.get(language)

    @property
    def supported_languages(self) -> frozenset[ProgrammingLanguage]:
        """Languages that currently have a registered parser."""
        return frozenset(self._parsers)

    def parse(self, file_metadata: FileMetadata) -> ParseResult:
        """Dispatch ``file_metadata`` to the parser for its language.

        Never raises for unsupported languages or parser failures; the
        outcome is always encoded in the returned ParseResult.
        """
        parser = self._parsers.get(file_metadata.language)
        if parser is None:
            logger.debug(
                "No parser registered for %s (%s)",
                file_metadata.language,
                file_metadata.relative_path,
            )
            return ParseResult(
                file_path=file_metadata.relative_path,
                language=file_metadata.language,
                status=ParseStatus.UNSUPPORTED_LANGUAGE,
                message=f"No parser registered for language: {file_metadata.language.value}",
            )
        try:
            return parser.parse(file_metadata)
        except Exception as exc:  # defensive: parsers should not raise
            logger.exception(
                "Parser %s raised for %s",
                type(parser).__name__,
                file_metadata.relative_path,
            )
            return ParseResult(
                file_path=file_metadata.relative_path,
                language=file_metadata.language,
                status=ParseStatus.ERROR,
                message=f"Parser raised an unexpected error: {exc}",
            )


def create_default_manager() -> ParserManager:
    """Build a ParserManager with all built-in parsers registered."""
    manager = ParserManager()
    manager.register(PythonParser())
    return manager

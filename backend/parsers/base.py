"""Common interface that every language parser must implement."""

from abc import ABC, abstractmethod
from typing import ClassVar

from parsers.models import ParseResult
from scanner.language import ProgrammingLanguage
from scanner.models import FileMetadata


class BaseParser(ABC):
    """Abstract base class for language parsers.

    Subclasses declare the language they handle via the ``language`` class
    attribute and implement :meth:`parse`. Implementations must not raise
    for ordinary parse failures — they report problems through
    :class:`ParseResult` instead.
    """

    language: ClassVar[ProgrammingLanguage]

    @abstractmethod
    def parse(self, file_metadata: FileMetadata) -> ParseResult:
        """Parse one file and return a :class:`ParseResult`."""
        raise NotImplementedError

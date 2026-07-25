"""Strongly typed results returned by every parser."""

from enum import StrEnum

from pydantic import BaseModel, Field

from parsers.imports import Import
from parsers.symbols import Symbol
from scanner.language import ProgrammingLanguage


class ParseStatus(StrEnum):
    """Outcome of a parse attempt."""

    SUCCESS = "success"
    NOT_IMPLEMENTED = "not_implemented"
    UNSUPPORTED_LANGUAGE = "unsupported_language"
    ERROR = "error"


class ParseResult(BaseModel):
    """Result of parsing (or attempting to parse) a single file."""

    file_path: str
    language: ProgrammingLanguage
    status: ParseStatus
    message: str = ""
    error_line: int | None = None
    error_column: int | None = None
    symbols: list[Symbol] = Field(default_factory=list)
    imports: list[Import] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when parsing completed successfully."""
        return self.status is ParseStatus.SUCCESS

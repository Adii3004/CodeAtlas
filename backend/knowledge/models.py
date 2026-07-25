"""Unified models describing everything known about a repository.

Syntax trees are deliberately absent: they live inside the parsers and are
never serialized as part of the knowledge model.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from parsers.imports import Import
from parsers.models import ParseStatus
from parsers.symbols import Symbol
from scanner.classifier import FileCategory
from scanner.inventory import RepositoryInventory
from scanner.language import ProgrammingLanguage
from scanner.models import FileMetadata


class CodeFile(BaseModel):
    """Everything currently known about one file in the repository."""

    metadata: FileMetadata
    parse_status: ParseStatus
    parse_message: str = ""
    error_line: int | None = None
    error_column: int | None = None
    symbols: list[Symbol] = Field(default_factory=list)
    imports: list[Import] = Field(default_factory=list)

    @property
    def relative_path(self) -> str:
        """Repository-relative path of the file."""
        return self.metadata.relative_path

    @property
    def category(self) -> FileCategory:
        """File category from classification."""
        return self.metadata.category

    @property
    def language(self) -> ProgrammingLanguage:
        """Programming language from detection."""
        return self.metadata.language

    @property
    def is_parsed(self) -> bool:
        """True when the file was parsed successfully."""
        return self.parse_status is ParseStatus.SUCCESS


class RepositoryKnowledge(BaseModel):
    """One scanned repository: metadata, inventory, and every file."""

    repository_name: str
    root_path: str
    generated_at: datetime
    total_files: int
    total_size_bytes: int
    inventory: RepositoryInventory
    files: list[CodeFile]

    def get_file(self, relative_path: str) -> CodeFile | None:
        """Look up one file by its repository-relative path."""
        for code_file in self.files:
            if code_file.relative_path == relative_path:
                return code_file
        return None

    @property
    def parsed_files(self) -> list[CodeFile]:
        """Files that parsed successfully."""
        return [f for f in self.files if f.is_parsed]

    @property
    def total_symbols(self) -> int:
        """Total extracted symbols across all files."""
        return sum(len(f.symbols) for f in self.files)

    @property
    def total_imports(self) -> int:
        """Total extracted imports across all files."""
        return sum(len(f.imports) for f in self.files)

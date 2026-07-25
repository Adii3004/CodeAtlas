"""Structured results produced by the repository scanner."""

from datetime import datetime

from pydantic import BaseModel

from scanner.classifier import FileCategory
from scanner.language import ProgrammingLanguage


class FileMetadata(BaseModel):
    """Metadata for a single discovered file. Contents are never read."""

    absolute_path: str
    relative_path: str
    filename: str
    extension: str
    size_bytes: int
    last_modified: datetime
    category: FileCategory
    language: ProgrammingLanguage


class ScanResult(BaseModel):
    """Outcome of scanning one repository root."""

    root_path: str
    total_files: int
    total_size_bytes: int
    files: list[FileMetadata]

"""Repository scanner package: filesystem discovery without content parsing."""

from scanner.classifier import FileCategory, classify_file
from scanner.inventory import DirectoryStats, RepositoryInventory, build_inventory
from scanner.language import ProgrammingLanguage, detect_language
from scanner.models import FileMetadata, ScanResult
from scanner.repository_scanner import (
    DEFAULT_IGNORED_DIRS,
    DEFAULT_IGNORED_FILE_PATTERNS,
    RepositoryScanner,
    ScanError,
)

__all__ = [
    "DEFAULT_IGNORED_DIRS",
    "DEFAULT_IGNORED_FILE_PATTERNS",
    "DirectoryStats",
    "FileCategory",
    "FileMetadata",
    "ProgrammingLanguage",
    "RepositoryInventory",
    "RepositoryScanner",
    "ScanError",
    "ScanResult",
    "build_inventory",
    "classify_file",
    "detect_language",
]

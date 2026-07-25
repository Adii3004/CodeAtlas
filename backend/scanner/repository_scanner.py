"""Recursive repository scanner.

Discovers files and folders and returns structured metadata only — it never
reads file contents, parses source code, or follows symbolic links.
"""

import logging
from collections.abc import Iterable, Iterator
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path

from scanner.classifier import classify_file
from scanner.language import detect_language
from scanner.models import FileMetadata, ScanResult

logger = logging.getLogger(__name__)

DEFAULT_IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        "build",
        "dist",
        ".idea",
        ".vscode",
    }
)

DEFAULT_IGNORED_FILE_PATTERNS: tuple[str, ...] = ("*.pyc", "*.pyo", "*.log")


class ScanError(ValueError):
    """Raised when a repository path cannot be scanned."""


class RepositoryScanner:
    """Reusable, framework-independent filesystem scanner.

    Ignore rules are configurable per instance; the defaults cover common
    VCS, virtualenv, dependency, and build directories.
    """

    def __init__(
        self,
        ignored_dirs: Iterable[str] | None = None,
        ignored_file_patterns: Iterable[str] | None = None,
    ) -> None:
        self.ignored_dirs: frozenset[str] = frozenset(
            ignored_dirs if ignored_dirs is not None else DEFAULT_IGNORED_DIRS
        )
        self.ignored_file_patterns: tuple[str, ...] = tuple(
            ignored_file_patterns
            if ignored_file_patterns is not None
            else DEFAULT_IGNORED_FILE_PATTERNS
        )

    def scan(self, repo_path: str | Path) -> ScanResult:
        """Recursively scan ``repo_path`` and return metadata for every file.

        Raises:
            ScanError: if the path does not exist or is not a directory.
        """
        root = Path(repo_path)
        if not root.exists():
            raise ScanError(f"Repository path does not exist: {root}")
        if not root.is_dir():
            raise ScanError(f"Repository path is not a directory: {root}")
        root = root.resolve()

        logger.info("Scanning repository: %s", root)
        files = sorted(self._walk(root, root), key=lambda f: f.relative_path)
        total_size = sum(f.size_bytes for f in files)
        logger.info(
            "Scan complete: %d files, %d bytes in %s", len(files), total_size, root
        )
        return ScanResult(
            root_path=str(root),
            total_files=len(files),
            total_size_bytes=total_size,
            files=files,
        )

    def _walk(self, directory: Path, root: Path) -> Iterator[FileMetadata]:
        """Yield metadata for files under ``directory``, pruning ignored dirs."""
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            logger.warning("Skipping unreadable directory %s: %s", directory, exc)
            return

        for entry in entries:
            if entry.is_symlink():
                logger.debug("Skipping symbolic link: %s", entry)
                continue
            if entry.is_dir():
                if entry.name in self.ignored_dirs:
                    logger.debug("Skipping ignored directory: %s", entry)
                    continue
                yield from self._walk(entry, root)
            elif entry.is_file():
                if self._is_ignored_file(entry.name):
                    logger.debug("Skipping ignored file: %s", entry)
                    continue
                metadata = self._collect_metadata(entry, root)
                if metadata is not None:
                    yield metadata

    def _is_ignored_file(self, filename: str) -> bool:
        """Return True if ``filename`` matches any ignored file pattern."""
        return any(fnmatch(filename, pattern) for pattern in self.ignored_file_patterns)

    @staticmethod
    def _collect_metadata(file_path: Path, root: Path) -> FileMetadata | None:
        """Build metadata for one file without reading its contents."""
        try:
            stat = file_path.stat()
        except OSError as exc:
            logger.warning("Skipping unreadable file %s: %s", file_path, exc)
            return None
        relative_path = file_path.relative_to(root)
        return FileMetadata(
            absolute_path=str(file_path),
            relative_path=relative_path.as_posix(),
            filename=file_path.name,
            extension=file_path.suffix.lower(),
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime),
            category=classify_file(relative_path),
            language=detect_language(relative_path),
        )

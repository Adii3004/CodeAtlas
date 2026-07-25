"""Repository inventory: statistics computed from a ScanResult.

Pure aggregation over already-collected metadata — this module never touches
the filesystem, never reads file contents, and knows nothing about FastAPI.
"""

import logging
from collections import Counter
from pathlib import Path, PurePosixPath

from pydantic import BaseModel

from scanner.classifier import FileCategory
from scanner.language import ProgrammingLanguage
from scanner.models import FileMetadata, ScanResult

logger = logging.getLogger(__name__)

#: Key used in extension counts for files without an extension.
NO_EXTENSION_KEY = "(none)"

#: Path used for the repository root directory in directory statistics.
ROOT_DIRECTORY_KEY = "."


class DirectoryStats(BaseModel):
    """Statistics for one directory within the repository.

    ``direct_file_count`` counts files immediately inside the directory;
    ``total_file_count`` and ``total_size_bytes`` are cumulative and include
    all subdirectories.
    """

    path: str
    direct_file_count: int
    total_file_count: int
    total_size_bytes: int


class RepositoryInventory(BaseModel):
    """Summary statistics for a scanned repository."""

    repository_name: str
    root_path: str
    total_files: int
    total_size_bytes: int
    category_counts: dict[FileCategory, int]
    language_counts: dict[ProgrammingLanguage, int]
    extension_counts: dict[str, int]
    largest_files: list[FileMetadata]
    largest_directories: list[DirectoryStats]
    directory_stats: list[DirectoryStats]


def build_inventory(
    scan_result: ScanResult,
    *,
    largest_files_limit: int = 10,
    largest_directories_limit: int = 10,
) -> RepositoryInventory:
    """Build a :class:`RepositoryInventory` from a :class:`ScanResult`.

    ``category_counts`` always contains every category (zero-filled) so
    consumers have stable keys; ``language_counts`` and ``extension_counts``
    only contain observed values, ordered by count descending, then name.
    ``largest_directories`` is ranked by *direct* file count.
    """
    files = scan_result.files
    root = Path(scan_result.root_path)
    repository_name = root.name or str(root)

    category_counts: dict[FileCategory, int] = {cat: 0 for cat in FileCategory}
    language_counter: Counter[ProgrammingLanguage] = Counter()
    extension_counter: Counter[str] = Counter()
    for meta in files:
        category_counts[meta.category] += 1
        language_counter[meta.language] += 1
        extension_counter[meta.extension or NO_EXTENSION_KEY] += 1

    directory_stats = _build_directory_stats(files)
    largest_directories = sorted(
        (d for d in directory_stats if d.direct_file_count > 0),
        key=lambda d: (-d.direct_file_count, d.path),
    )[:largest_directories_limit]

    largest_files = sorted(files, key=lambda f: (-f.size_bytes, f.relative_path))[
        :largest_files_limit
    ]

    inventory = RepositoryInventory(
        repository_name=repository_name,
        root_path=scan_result.root_path,
        total_files=scan_result.total_files,
        total_size_bytes=scan_result.total_size_bytes,
        category_counts=category_counts,
        language_counts=dict(_sorted_by_count(language_counter)),
        extension_counts=dict(_sorted_by_count(extension_counter)),
        largest_files=largest_files,
        largest_directories=largest_directories,
        directory_stats=directory_stats,
    )
    logger.info(
        "Inventory built for %s: %d files across %d directories",
        repository_name,
        inventory.total_files,
        len(directory_stats),
    )
    return inventory


def _build_directory_stats(files: list[FileMetadata]) -> list[DirectoryStats]:
    """Compute per-directory stats; cumulative values include subdirectories.

    Every directory that contains at least one file (directly or through a
    subdirectory) is included; the repository root appears as ``"."``.
    """
    direct: Counter[str] = Counter()
    total: Counter[str] = Counter()
    size: Counter[str] = Counter()

    for meta in files:
        parent = PurePosixPath(meta.relative_path).parent
        direct[parent.as_posix()] += 1
        while True:
            key = parent.as_posix()
            total[key] += 1
            size[key] += meta.size_bytes
            if key == ROOT_DIRECTORY_KEY:
                break
            parent = parent.parent

    return [
        DirectoryStats(
            path=path,
            direct_file_count=direct.get(path, 0),
            total_file_count=total[path],
            total_size_bytes=size[path],
        )
        for path in sorted(total)
    ]


def _sorted_by_count(counter: Counter) -> list[tuple[object, int]]:
    """Order counter items by count descending, then key ascending."""
    return sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))

"""File classification based on extension, filename, and path only.

File contents are never read. Classification rules are applied in priority
order: exact filenames, well-known name stems, test conventions, then the
extension map, falling back to UNKNOWN.
"""

import logging
from enum import StrEnum
from pathlib import PurePath

logger = logging.getLogger(__name__)


class FileCategory(StrEnum):
    """What kind of file a discovered path represents."""

    SOURCE_CODE = "source_code"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    DATA = "data"
    TEST = "test"
    SCRIPT = "script"
    IMAGE = "image"
    ARCHIVE = "archive"
    BINARY = "binary"
    UNKNOWN = "unknown"


# Exact filenames (lowercase) that override extension-based rules.
_FILENAME_MAP: dict[str, FileCategory] = {
    "dockerfile": FileCategory.CONFIGURATION,
    "docker-compose.yml": FileCategory.CONFIGURATION,
    "docker-compose.yaml": FileCategory.CONFIGURATION,
    "makefile": FileCategory.CONFIGURATION,
    "requirements.txt": FileCategory.CONFIGURATION,
    "pyproject.toml": FileCategory.CONFIGURATION,
    "package.json": FileCategory.CONFIGURATION,
    "package-lock.json": FileCategory.CONFIGURATION,
    "tsconfig.json": FileCategory.CONFIGURATION,
    ".gitignore": FileCategory.CONFIGURATION,
    ".gitattributes": FileCategory.CONFIGURATION,
    ".editorconfig": FileCategory.CONFIGURATION,
}

# Well-known documentation name stems (README, README.md, license.txt, ...).
_DOCUMENTATION_STEMS: frozenset[str] = frozenset(
    {"readme", "license", "licence", "changelog", "contributing", "authors", "notice"}
)

_EXTENSION_MAP: dict[str, FileCategory] = {
    # Source code
    ".py": FileCategory.SOURCE_CODE,
    ".pyi": FileCategory.SOURCE_CODE,
    ".ts": FileCategory.SOURCE_CODE,
    ".tsx": FileCategory.SOURCE_CODE,
    ".js": FileCategory.SOURCE_CODE,
    ".jsx": FileCategory.SOURCE_CODE,
    ".mjs": FileCategory.SOURCE_CODE,
    ".cjs": FileCategory.SOURCE_CODE,
    ".java": FileCategory.SOURCE_CODE,
    ".c": FileCategory.SOURCE_CODE,
    ".h": FileCategory.SOURCE_CODE,
    ".cpp": FileCategory.SOURCE_CODE,
    ".cc": FileCategory.SOURCE_CODE,
    ".hpp": FileCategory.SOURCE_CODE,
    ".cs": FileCategory.SOURCE_CODE,
    ".go": FileCategory.SOURCE_CODE,
    ".rs": FileCategory.SOURCE_CODE,
    ".rb": FileCategory.SOURCE_CODE,
    ".php": FileCategory.SOURCE_CODE,
    ".kt": FileCategory.SOURCE_CODE,
    ".swift": FileCategory.SOURCE_CODE,
    ".scala": FileCategory.SOURCE_CODE,
    ".vue": FileCategory.SOURCE_CODE,
    ".sql": FileCategory.SOURCE_CODE,
    ".css": FileCategory.SOURCE_CODE,
    ".scss": FileCategory.SOURCE_CODE,
    ".html": FileCategory.SOURCE_CODE,
    # Configuration
    ".toml": FileCategory.CONFIGURATION,
    ".yaml": FileCategory.CONFIGURATION,
    ".yml": FileCategory.CONFIGURATION,
    ".ini": FileCategory.CONFIGURATION,
    ".cfg": FileCategory.CONFIGURATION,
    ".conf": FileCategory.CONFIGURATION,
    ".properties": FileCategory.CONFIGURATION,
    # Documentation
    ".md": FileCategory.DOCUMENTATION,
    ".rst": FileCategory.DOCUMENTATION,
    ".adoc": FileCategory.DOCUMENTATION,
    ".txt": FileCategory.DOCUMENTATION,
    # Data
    ".json": FileCategory.DATA,
    ".jsonl": FileCategory.DATA,
    ".csv": FileCategory.DATA,
    ".tsv": FileCategory.DATA,
    ".xml": FileCategory.DATA,
    ".parquet": FileCategory.DATA,
    # Scripts
    ".sh": FileCategory.SCRIPT,
    ".bash": FileCategory.SCRIPT,
    ".zsh": FileCategory.SCRIPT,
    ".ps1": FileCategory.SCRIPT,
    ".bat": FileCategory.SCRIPT,
    ".cmd": FileCategory.SCRIPT,
    # Images
    ".png": FileCategory.IMAGE,
    ".jpg": FileCategory.IMAGE,
    ".jpeg": FileCategory.IMAGE,
    ".gif": FileCategory.IMAGE,
    ".svg": FileCategory.IMAGE,
    ".ico": FileCategory.IMAGE,
    ".webp": FileCategory.IMAGE,
    ".bmp": FileCategory.IMAGE,
    # Archives
    ".zip": FileCategory.ARCHIVE,
    ".tar": FileCategory.ARCHIVE,
    ".gz": FileCategory.ARCHIVE,
    ".tgz": FileCategory.ARCHIVE,
    ".bz2": FileCategory.ARCHIVE,
    ".xz": FileCategory.ARCHIVE,
    ".rar": FileCategory.ARCHIVE,
    ".7z": FileCategory.ARCHIVE,
    # Binaries
    ".exe": FileCategory.BINARY,
    ".dll": FileCategory.BINARY,
    ".so": FileCategory.BINARY,
    ".dylib": FileCategory.BINARY,
    ".bin": FileCategory.BINARY,
    ".o": FileCategory.BINARY,
    ".obj": FileCategory.BINARY,
    ".class": FileCategory.BINARY,
    ".jar": FileCategory.BINARY,
    ".wasm": FileCategory.BINARY,
    ".pyd": FileCategory.BINARY,
}

# Extensions whose files count as tests when test naming/path conventions match.
_TESTABLE_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".go", ".rs", ".rb", ".cs"}
)

_TEST_DIR_NAMES: frozenset[str] = frozenset({"test", "tests", "__tests__"})


def classify_file(path: str | PurePath) -> FileCategory:
    """Classify a file by its path alone; contents are never read.

    ``path`` may be absolute, relative, or a bare filename. Matching is
    case-insensitive. Priority: exact filenames > ``.env`` family >
    documentation stems (README, LICENSE, ...) > test conventions
    (``test_*``/``*_test`` names, ``.test``/``.spec`` infixes, or a
    ``tests``/``test``/``__tests__`` directory, for source-code files) >
    extension map > UNKNOWN.
    """
    pure = PurePath(path)
    filename = pure.name.lower()
    extension = pure.suffix.lower()
    stem = pure.stem.lower()

    if filename in _FILENAME_MAP:
        return _FILENAME_MAP[filename]

    if filename.startswith(".env"):
        return FileCategory.CONFIGURATION

    # README, LICENSE, CHANGELOG etc., with or without an extension.
    if stem in _DOCUMENTATION_STEMS or filename in _DOCUMENTATION_STEMS:
        return FileCategory.DOCUMENTATION

    if extension in _TESTABLE_EXTENSIONS and _is_test_file(pure, stem):
        return FileCategory.TEST

    category = _EXTENSION_MAP.get(extension, FileCategory.UNKNOWN)
    if category is FileCategory.UNKNOWN:
        logger.debug("Unrecognized file type: %s", pure)
    return category


def _is_test_file(pure: PurePath, stem: str) -> bool:
    """Detect common test naming and directory conventions."""
    if stem.startswith("test_") or stem.endswith("_test"):
        return True
    # JS/TS style: app.test.ts, app.spec.tsx (stem is "app.test" / "app.spec").
    if stem.endswith((".test", ".spec")):
        return True
    parent_parts = {part.lower() for part in pure.parts[:-1]}
    return not parent_parts.isdisjoint(_TEST_DIR_NAMES)

"""Programming language detection from extension and filename only.

File contents are never read or parsed. Detection priority: special
filenames (Dockerfile, Makefile, LICENSE, ...) first, then the extension
map, falling back to UNKNOWN.
"""

import logging
from enum import StrEnum
from pathlib import PurePath

logger = logging.getLogger(__name__)


class ProgrammingLanguage(StrEnum):
    """Language of a file, detected from its path alone."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    C_SHARP = "csharp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    MARKDOWN = "markdown"
    SHELL = "shell"
    DOCKER = "docker"
    TEXT = "text"
    UNKNOWN = "unknown"


# Exact filenames (lowercase) checked before any extension rule.
_FILENAME_MAP: dict[str, ProgrammingLanguage] = {
    "dockerfile": ProgrammingLanguage.DOCKER,
    "makefile": ProgrammingLanguage.TEXT,
    "license": ProgrammingLanguage.TEXT,
    "licence": ProgrammingLanguage.TEXT,
    "notice": ProgrammingLanguage.TEXT,
    "authors": ProgrammingLanguage.TEXT,
    ".gitignore": ProgrammingLanguage.TEXT,
    ".gitattributes": ProgrammingLanguage.TEXT,
}

_EXTENSION_MAP: dict[str, ProgrammingLanguage] = {
    ".py": ProgrammingLanguage.PYTHON,
    ".pyi": ProgrammingLanguage.PYTHON,
    ".pyw": ProgrammingLanguage.PYTHON,
    ".js": ProgrammingLanguage.JAVASCRIPT,
    ".jsx": ProgrammingLanguage.JAVASCRIPT,
    ".mjs": ProgrammingLanguage.JAVASCRIPT,
    ".cjs": ProgrammingLanguage.JAVASCRIPT,
    ".ts": ProgrammingLanguage.TYPESCRIPT,
    ".tsx": ProgrammingLanguage.TYPESCRIPT,
    ".mts": ProgrammingLanguage.TYPESCRIPT,
    ".cts": ProgrammingLanguage.TYPESCRIPT,
    ".java": ProgrammingLanguage.JAVA,
    ".cpp": ProgrammingLanguage.CPP,
    ".cc": ProgrammingLanguage.CPP,
    ".cxx": ProgrammingLanguage.CPP,
    ".hpp": ProgrammingLanguage.CPP,
    ".hh": ProgrammingLanguage.CPP,
    ".c": ProgrammingLanguage.C,
    ".h": ProgrammingLanguage.C,
    ".cs": ProgrammingLanguage.C_SHARP,
    ".go": ProgrammingLanguage.GO,
    ".rs": ProgrammingLanguage.RUST,
    ".php": ProgrammingLanguage.PHP,
    ".rb": ProgrammingLanguage.RUBY,
    ".swift": ProgrammingLanguage.SWIFT,
    ".kt": ProgrammingLanguage.KOTLIN,
    ".kts": ProgrammingLanguage.KOTLIN,
    ".html": ProgrammingLanguage.HTML,
    ".htm": ProgrammingLanguage.HTML,
    ".css": ProgrammingLanguage.CSS,
    ".scss": ProgrammingLanguage.CSS,
    ".sass": ProgrammingLanguage.CSS,
    ".json": ProgrammingLanguage.JSON,
    ".jsonl": ProgrammingLanguage.JSON,
    ".yml": ProgrammingLanguage.YAML,
    ".yaml": ProgrammingLanguage.YAML,
    ".xml": ProgrammingLanguage.XML,
    ".md": ProgrammingLanguage.MARKDOWN,
    ".markdown": ProgrammingLanguage.MARKDOWN,
    ".sh": ProgrammingLanguage.SHELL,
    ".bash": ProgrammingLanguage.SHELL,
    ".zsh": ProgrammingLanguage.SHELL,
    ".txt": ProgrammingLanguage.TEXT,
    ".rst": ProgrammingLanguage.TEXT,
}


def detect_language(path: str | PurePath) -> ProgrammingLanguage:
    """Detect the programming language of a file from its path alone.

    ``path`` may be absolute, relative, or a bare filename. Matching is
    case-insensitive. Special filenames win over extensions (``Dockerfile``
    → DOCKER even though it has no extension; ``Dockerfile.dev`` also
    matches). Files with no rule return UNKNOWN.
    """
    pure = PurePath(path)
    filename = pure.name.lower()
    extension = pure.suffix.lower()

    if filename in _FILENAME_MAP:
        return _FILENAME_MAP[filename]

    # Dockerfile variants: Dockerfile.dev, Dockerfile.prod, dev.Dockerfile.
    if filename.startswith("dockerfile.") or extension == ".dockerfile":
        return ProgrammingLanguage.DOCKER

    language = _EXTENSION_MAP.get(extension, ProgrammingLanguage.UNKNOWN)
    if language is ProgrammingLanguage.UNKNOWN:
        logger.debug("Unrecognized language for file: %s", pure)
    return language

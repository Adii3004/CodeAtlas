"""Python parser built on Tree-sitter.

This parser only validates that a file parses: it reads the source, runs it
through the official tree-sitter-python grammar, and reports SUCCESS or
ERROR. The produced syntax tree is stored internally for the next milestone;
it is not analyzed and no symbols are extracted.
"""

import io
import logging
import tokenize
from typing import ClassVar

import tree_sitter_python
from tree_sitter import Language, Node, Parser, Tree

from parsers.base import BaseParser
from parsers.imports import extract_imports
from parsers.models import ParseResult, ParseStatus
from parsers.symbols import extract_top_level_symbols
from scanner.language import ProgrammingLanguage
from scanner.models import FileMetadata

logger = logging.getLogger(__name__)

_PYTHON_LANGUAGE = Language(tree_sitter_python.language())


class PythonParser(BaseParser):
    """Parses Python source files with Tree-sitter."""

    language: ClassVar[ProgrammingLanguage] = ProgrammingLanguage.PYTHON

    def __init__(self) -> None:
        self._parser = Parser(_PYTHON_LANGUAGE)
        # Syntax trees per relative path, kept for the next milestone
        # (symbol extraction). Not part of the public API.
        self._trees: dict[str, Tree] = {}

    def parse(self, file_metadata: FileMetadata) -> ParseResult:
        """Parse one Python file and extract symbols and imports."""
        try:
            source = self._read_source_utf8(file_metadata.absolute_path)
        except OSError as exc:
            logger.warning("Cannot read %s: %s", file_metadata.absolute_path, exc)
            return ParseResult(
                file_path=file_metadata.relative_path,
                language=self.language,
                status=ParseStatus.ERROR,
                message=f"Cannot read file: {exc}",
            )
        except (SyntaxError, UnicodeDecodeError, LookupError) as exc:
            # Bad or unknown PEP 263 coding declaration / undecodable bytes.
            return ParseResult(
                file_path=file_metadata.relative_path,
                language=self.language,
                status=ParseStatus.ERROR,
                message=f"Cannot decode file: {exc}",
            )

        tree = self._parser.parse(source)
        self._trees[file_metadata.relative_path] = tree

        if tree.root_node.has_error:
            error_node = self._find_first_error(tree.root_node)
            line = error_node.start_point.row + 1 if error_node else None
            column = error_node.start_point.column + 1 if error_node else None
            logger.debug(
                "Syntax error in %s at line %s",
                file_metadata.relative_path,
                line,
            )
            return ParseResult(
                file_path=file_metadata.relative_path,
                language=self.language,
                status=ParseStatus.ERROR,
                message=f"Syntax error (line {line}, column {column})",
                error_line=line,
                error_column=column,
            )

        return ParseResult(
            file_path=file_metadata.relative_path,
            language=self.language,
            status=ParseStatus.SUCCESS,
            message="Parsed successfully",
            symbols=extract_top_level_symbols(tree, file_metadata.relative_path),
            imports=extract_imports(tree, file_metadata.relative_path),
        )

    def get_tree(self, source: FileMetadata | ParseResult) -> Tree | None:
        """Return the stored syntax tree for a previously parsed file.

        Takes the metadata or parse result object rather than a raw path
        string, so callers stay correct if path handling changes later.
        """
        if isinstance(source, FileMetadata):
            return self._trees.get(source.relative_path)
        return self._trees.get(source.file_path)

    @staticmethod
    def _read_source_utf8(absolute_path: str) -> bytes:
        """Read Python source and return UTF-8 bytes for Tree-sitter.

        Tree-sitter expects UTF-8 input, so sources with a PEP 263 coding
        declaration (e.g. latin-1) are decoded per their declared encoding
        and re-encoded. ``tokenize.detect_encoding`` also handles BOMs.
        """
        with open(absolute_path, "rb") as handle:
            raw = handle.read()
        encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
        if encoding.replace("-", "").lower() == "utf8":
            return raw
        return raw.decode(encoding).encode("utf-8")

    @staticmethod
    def _find_first_error(root: Node) -> Node | None:
        """Return the first ERROR or missing node in document order."""
        if not root.has_error:
            return None
        stack = [root]
        first: Node | None = None
        while stack:
            node = stack.pop()
            if node.type == "ERROR" or node.is_missing:
                if first is None or node.start_byte < first.start_byte:
                    first = node
                continue
            if node.has_error:
                stack.extend(node.children)
        return first

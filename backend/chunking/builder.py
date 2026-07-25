"""ChunkBuilder: turns RepositoryKnowledge into RepositoryChunks.

Rules:

- Python files: one FILE_SUMMARY, one CLASS chunk per top-level class, one
  FUNCTION chunk per top-level (async) function, and a MODULE chunk only
  when the file has no symbols at all (skipped for empty files).
- Markdown files: one DOCUMENTATION chunk per heading section (plus one for
  any preamble before the first heading).
- All other files are ignored for now.
"""

import hashlib
import logging
import re

from chunking.models import Chunk, ChunkType, RepositoryChunks, estimate_tokens
from graph.resolver import ModuleResolver
from knowledge.models import CodeFile, RepositoryKnowledge
from parsers.imports import Import
from parsers.symbols import SymbolType
from scanner.language import ProgrammingLanguage

logger = logging.getLogger(__name__)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

_SYMBOL_CHUNK_TYPES: dict[SymbolType, ChunkType] = {
    SymbolType.CLASS: ChunkType.CLASS,
    SymbolType.FUNCTION: ChunkType.FUNCTION,
    SymbolType.ASYNC_FUNCTION: ChunkType.FUNCTION,
}


class ChunkBuilder:
    """Builds deterministic chunks from a RepositoryKnowledge."""

    def build(self, knowledge: RepositoryKnowledge) -> RepositoryChunks:
        """Build all chunks for one repository."""
        resolver = ModuleResolver(knowledge.files)
        chunks: list[Chunk] = []
        for code_file in knowledge.files:
            if code_file.language is ProgrammingLanguage.PYTHON:
                chunks.extend(self._chunk_python_file(knowledge, code_file, resolver))
            elif code_file.language is ProgrammingLanguage.MARKDOWN:
                chunks.extend(self._chunk_markdown_file(knowledge, code_file))

        result = RepositoryChunks(
            repository_name=knowledge.repository_name, chunks=chunks
        )
        logger.info(
            "Chunking complete for %s: %d chunks from %d files",
            knowledge.repository_name,
            result.total_chunks,
            knowledge.total_files,
        )
        return result

    # ------------------------------------------------------------------ python

    def _chunk_python_file(
        self,
        knowledge: RepositoryKnowledge,
        code_file: CodeFile,
        resolver: ModuleResolver,
    ) -> list[Chunk]:
        lines = self._read_lines(code_file)
        if lines is None:
            return []

        imports = sorted(
            {text for imp in code_file.imports if (text := _import_text(imp))}
        )
        dependencies = sorted(
            {
                resolved
                for imp in code_file.imports
                if (resolved := resolver.resolve(code_file.relative_path, imp))
                is not None
                and resolved != code_file.relative_path
            }
        )

        def make(
            chunk_type: ChunkType,
            content: str,
            start_line: int,
            end_line: int,
            symbol_name: str | None = None,
            qualified_name: str | None = None,
        ) -> Chunk:
            return Chunk(
                chunk_id=_chunk_id(
                    knowledge.repository_name,
                    code_file.relative_path,
                    chunk_type,
                    symbol_name,
                    start_line,
                    end_line,
                ),
                repository_name=knowledge.repository_name,
                relative_path=code_file.relative_path,
                language=code_file.language,
                category=code_file.category,
                chunk_type=chunk_type,
                symbol_name=symbol_name,
                qualified_name=qualified_name,
                start_line=start_line,
                end_line=end_line,
                content=content,
                token_estimate=estimate_tokens(content),
                imports=imports,
                dependencies=dependencies,
            )

        total_lines = max(len(lines), 1)
        chunks = [
            make(
                ChunkType.FILE_SUMMARY,
                self._file_summary_text(code_file, imports, dependencies),
                1,
                total_lines,
            )
        ]

        for symbol in code_file.symbols:
            chunk_type = _SYMBOL_CHUNK_TYPES.get(symbol.symbol_type)
            if chunk_type is None:
                continue
            content = "\n".join(lines[symbol.start_line - 1 : symbol.end_line])
            chunks.append(
                make(
                    chunk_type,
                    content,
                    symbol.start_line,
                    symbol.end_line,
                    symbol_name=symbol.name,
                    qualified_name=symbol.qualified_name,
                )
            )

        if not code_file.symbols:
            content = "\n".join(lines)
            if content.strip():
                chunks.append(make(ChunkType.MODULE, content, 1, len(lines)))
        return chunks

    @staticmethod
    def _file_summary_text(
        code_file: CodeFile, imports: list[str], dependencies: list[str]
    ) -> str:
        classes = [
            s.name for s in code_file.symbols if s.symbol_type is SymbolType.CLASS
        ]
        functions = [
            s.name
            for s in code_file.symbols
            if s.symbol_type in (SymbolType.FUNCTION, SymbolType.ASYNC_FUNCTION)
        ]
        lines = [
            f"File: {code_file.relative_path}",
            f"Language: {code_file.language.value} | "
            f"Category: {code_file.category.value}",
            f"Classes: {', '.join(classes) if classes else '(none)'}",
            f"Functions: {', '.join(functions) if functions else '(none)'}",
            f"Imports: {', '.join(imports) if imports else '(none)'}",
            f"Repository dependencies: "
            f"{', '.join(dependencies) if dependencies else '(none)'}",
        ]
        return "\n".join(lines)

    # ---------------------------------------------------------------- markdown

    def _chunk_markdown_file(
        self, knowledge: RepositoryKnowledge, code_file: CodeFile
    ) -> list[Chunk]:
        lines = self._read_lines(code_file)
        if lines is None:
            return []

        sections = _split_markdown_sections(lines)
        chunks: list[Chunk] = []
        for heading, start_line, end_line in sections:
            content = "\n".join(lines[start_line - 1 : end_line])
            if not content.strip():
                continue
            chunks.append(
                Chunk(
                    chunk_id=_chunk_id(
                        knowledge.repository_name,
                        code_file.relative_path,
                        ChunkType.DOCUMENTATION,
                        heading,
                        start_line,
                        end_line,
                    ),
                    repository_name=knowledge.repository_name,
                    relative_path=code_file.relative_path,
                    language=code_file.language,
                    category=code_file.category,
                    chunk_type=ChunkType.DOCUMENTATION,
                    symbol_name=heading,
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    token_estimate=estimate_tokens(content),
                )
            )
        return chunks

    # ------------------------------------------------------------------ shared

    @staticmethod
    def _read_lines(code_file: CodeFile) -> list[str] | None:
        try:
            text = open(
                code_file.metadata.absolute_path,
                encoding="utf-8",
                errors="replace",
            ).read()
        except OSError as exc:
            logger.warning(
                "Skipping unreadable file %s: %s",
                code_file.metadata.absolute_path,
                exc,
            )
            return None
        return text.splitlines()


def _split_markdown_sections(
    lines: list[str],
) -> list[tuple[str | None, int, int]]:
    """Split markdown lines into (heading, start_line, end_line) sections.

    Content before the first heading becomes a section with heading None.
    Lines are 1-based; each section runs up to the line before the next
    heading.
    """
    boundaries: list[tuple[str | None, int]] = []
    for number, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if match:
            boundaries.append((match.group(2).strip(), number))

    if not boundaries:
        return [(None, 1, len(lines))] if lines else []

    sections: list[tuple[str | None, int, int]] = []
    first_heading_line = boundaries[0][1]
    if first_heading_line > 1:
        sections.append((None, 1, first_heading_line - 1))
    for index, (heading, start) in enumerate(boundaries):
        end = (
            boundaries[index + 1][1] - 1 if index + 1 < len(boundaries) else len(lines)
        )
        sections.append((heading, start, end))
    return sections


def _import_text(imp: Import) -> str:
    """Readable module reference for an Import (dots mark relative level)."""
    base = "." * imp.relative_level + (imp.module or "")
    if not imp.module and imp.name and imp.relative_level:
        return base + imp.name
    return base


def _chunk_id(
    repository_name: str,
    relative_path: str,
    chunk_type: ChunkType,
    symbol_name: str | None,
    start_line: int,
    end_line: int,
) -> str:
    """Deterministic chunk id from stable chunk coordinates."""
    key = "|".join(
        (
            repository_name,
            relative_path,
            chunk_type.value,
            symbol_name or "",
            str(start_line),
            str(end_line),
        )
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

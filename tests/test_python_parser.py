"""Unit tests for the ast-based Python parser."""

from datetime import datetime
from pathlib import Path

import pytest

from parsers import ParseStatus, PythonParser
from scanner import FileCategory, FileMetadata, ProgrammingLanguage


@pytest.fixture
def parser() -> PythonParser:
    return PythonParser()


def _metadata_for(file_path: Path, root: Path) -> FileMetadata:
    stat = file_path.stat()
    return FileMetadata(
        absolute_path=str(file_path),
        relative_path=file_path.relative_to(root).as_posix(),
        filename=file_path.name,
        extension=file_path.suffix.lower(),
        size_bytes=stat.st_size,
        last_modified=datetime.fromtimestamp(stat.st_mtime),
        category=FileCategory.SOURCE_CODE,
        language=ProgrammingLanguage.PYTHON,
    )


def _write(tmp_path: Path, name: str, source: str | bytes) -> FileMetadata:
    file_path = tmp_path / name
    if isinstance(source, bytes):
        file_path.write_bytes(source)
    else:
        file_path.write_text(source, encoding="utf-8")
    return _metadata_for(file_path, tmp_path)


class TestValidPython:
    def test_valid_file_parses_successfully(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        meta = _write(
            tmp_path,
            "app.py",
            "def greet(name):\n    return f'hello {name}'\n\n\nclass App:\n    pass\n",
        )

        result = parser.parse(meta)

        assert result.status is ParseStatus.SUCCESS
        assert result.ok
        assert result.message == "Parsed successfully"
        assert result.error_line is None
        assert result.error_column is None
        assert [(s.name, s.symbol_type.value) for s in result.symbols] == [
            ("greet", "function"),
            ("App", "class"),
        ]

    def test_empty_file(self, parser: PythonParser, tmp_path: Path) -> None:
        meta = _write(tmp_path, "empty.py", "")

        result = parser.parse(meta)

        assert result.status is ParseStatus.SUCCESS

    def test_comments_only(self, parser: PythonParser, tmp_path: Path) -> None:
        meta = _write(tmp_path, "notes.py", "# just a comment\n# another comment\n")

        result = parser.parse(meta)

        assert result.status is ParseStatus.SUCCESS

    def test_unicode_source(self, parser: PythonParser, tmp_path: Path) -> None:
        meta = _write(
            tmp_path,
            "unicode.py",
            "gruß = 'héllo wörld'\nemoji = '🚀'\ndef größe():\n    return gruß\n",
        )

        result = parser.parse(meta)

        assert result.status is ParseStatus.SUCCESS

    def test_latin1_with_coding_cookie(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        # PEP 263 declaration is honored because the parser feeds bytes to ast.
        source = "# -*- coding: latin-1 -*-\nname = 'caf\xe9'\n".encode("latin-1")
        meta = _write(tmp_path, "legacy.py", source)

        result = parser.parse(meta)

        assert result.status is ParseStatus.SUCCESS


class TestSyntaxErrors:
    def test_syntax_error_reports_location(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        meta = _write(tmp_path, "broken.py", "def broken(:\n    pass\n")

        result = parser.parse(meta)

        assert result.status is ParseStatus.ERROR
        assert not result.ok
        assert "Syntax error" in result.message
        assert result.error_line == 1
        assert result.error_column is not None
        assert "line 1" in result.message

    def test_error_on_later_line(self, parser: PythonParser, tmp_path: Path) -> None:
        meta = _write(tmp_path, "later.py", "x = 1\ny = 2\nif True\n    z = 3\n")

        result = parser.parse(meta)

        assert result.status is ParseStatus.ERROR
        assert result.error_line == 3

    def test_missing_indentation_is_tolerated(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        meta = _write(tmp_path, "indent.py", "def f():\nreturn 1\n")

        result = parser.parse(meta)

        # Behavioral difference from ast: tree-sitter's error-tolerant
        # grammar accepts a def with no indented body, so this is SUCCESS
        # (ast raised IndentationError here).
        assert result.status is ParseStatus.SUCCESS


class TestUnreadableFiles:
    def test_missing_file_is_error_not_exception(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        meta = _write(tmp_path, "ghost.py", "x = 1\n")
        Path(meta.absolute_path).unlink()

        result = parser.parse(meta)

        assert result.status is ParseStatus.ERROR
        assert "Cannot read file" in result.message

    def test_null_bytes_are_error(self, parser: PythonParser, tmp_path: Path) -> None:
        meta = _write(tmp_path, "nulls.py", b"x = 1\x00\n")

        result = parser.parse(meta)

        assert result.status is ParseStatus.ERROR


class TestSyntaxTreeStorage:
    def test_tree_is_stored_after_successful_parse(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        meta = _write(tmp_path, "app.py", "x = 1\n")

        result = parser.parse(meta)

        assert result.status is ParseStatus.SUCCESS
        # Lookup works with either the metadata or the result object.
        for source in (meta, result):
            tree = parser.get_tree(source)
            assert tree is not None
            assert tree.root_node.type == "module"
            assert not tree.root_node.has_error

    def test_tree_stored_even_for_syntax_errors(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        # Tree-sitter always produces a (partial) tree; it is kept so the
        # next milestone can work with best-effort trees too.
        meta = _write(tmp_path, "broken.py", "def broken(:\n    pass\n")

        result = parser.parse(meta)

        assert result.status is ParseStatus.ERROR
        tree = parser.get_tree(result)
        assert tree is not None
        assert tree.root_node.has_error

    def test_no_tree_for_unparsed_file(
        self, parser: PythonParser, tmp_path: Path
    ) -> None:
        meta = _write(tmp_path, "never_parsed.py", "x = 1\n")
        assert parser.get_tree(meta) is None

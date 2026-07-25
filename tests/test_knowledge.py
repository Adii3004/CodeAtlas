"""Unit tests for the repository knowledge model and builder."""

from pathlib import Path

import pytest

from knowledge import RepositoryKnowledge, build_repository_knowledge
from parsers import ParseStatus, SymbolType
from scanner import FileCategory, ProgrammingLanguage, RepositoryScanner


@pytest.fixture
def scanner() -> RepositoryScanner:
    return RepositoryScanner()


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _build(scanner: RepositoryScanner, root: Path) -> RepositoryKnowledge:
    return build_repository_knowledge(scanner.scan(root))


class TestEmptyRepository:
    def test_empty_repository(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        knowledge = _build(scanner, tmp_path)

        assert knowledge.repository_name == tmp_path.resolve().name
        assert knowledge.root_path == str(tmp_path.resolve())
        assert knowledge.total_files == 0
        assert knowledge.total_size_bytes == 0
        assert knowledge.files == []
        assert knowledge.parsed_files == []
        assert knowledge.total_symbols == 0
        assert knowledge.total_imports == 0
        assert knowledge.inventory.total_files == 0


class TestSingleFile:
    def test_one_python_file(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "app.py",
            "import os\n\nclass App:\n    pass\n\ndef run():\n    pass\n",
        )

        knowledge = _build(scanner, tmp_path)

        assert knowledge.total_files == 1
        [code_file] = knowledge.files
        assert code_file.relative_path == "app.py"
        assert code_file.category is FileCategory.SOURCE_CODE
        assert code_file.language is ProgrammingLanguage.PYTHON
        assert code_file.parse_status is ParseStatus.SUCCESS
        assert code_file.is_parsed
        assert [(s.name, s.symbol_type) for s in code_file.symbols] == [
            ("App", SymbolType.CLASS),
            ("run", SymbolType.FUNCTION),
        ]
        assert [i.module for i in code_file.imports] == ["os"]
        assert knowledge.total_symbols == 2
        assert knowledge.total_imports == 1

    def test_get_file_lookup(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        _write(tmp_path, "src/module.py", "x = 1\n")

        knowledge = _build(scanner, tmp_path)

        assert knowledge.get_file("src/module.py") is not None
        assert knowledge.get_file("missing.py") is None


class TestMixedRepository:
    def test_mixed_files(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        _write(tmp_path, "main.py", "def main():\n    pass\n")
        _write(tmp_path, "README.md", "# Hello\n")
        _write(tmp_path, "config.yaml", "key: value\n")
        _write(tmp_path, "data.json", '{"a": 1}\n')

        knowledge = _build(scanner, tmp_path)

        assert knowledge.total_files == 4
        statuses = {f.relative_path: f.parse_status for f in knowledge.files}
        assert statuses == {
            "main.py": ParseStatus.SUCCESS,
            "README.md": ParseStatus.UNSUPPORTED_LANGUAGE,
            "config.yaml": ParseStatus.UNSUPPORTED_LANGUAGE,
            "data.json": ParseStatus.UNSUPPORTED_LANGUAGE,
        }
        assert len(knowledge.parsed_files) == 1
        # Inventory and files describe the same repository.
        assert knowledge.inventory.total_files == 4
        assert knowledge.inventory.language_counts[ProgrammingLanguage.PYTHON] == 1

    def test_unparsed_files_have_no_symbols_or_imports(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _write(tmp_path, "notes.md", "# notes\n")

        knowledge = _build(scanner, tmp_path)

        [code_file] = knowledge.files
        assert code_file.symbols == []
        assert code_file.imports == []
        assert not code_file.is_parsed


class TestParserErrors:
    def test_broken_python_file(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _write(tmp_path, "good.py", "def ok():\n    pass\n")
        _write(tmp_path, "broken.py", "def broken(:\n    pass\n")

        knowledge = _build(scanner, tmp_path)

        broken = knowledge.get_file("broken.py")
        assert broken is not None
        assert broken.parse_status is ParseStatus.ERROR
        assert broken.error_line == 1
        assert "Syntax error" in broken.parse_message
        assert broken.symbols == []

        good = knowledge.get_file("good.py")
        assert good is not None
        assert good.is_parsed
        assert knowledge.total_symbols == 1  # only from good.py

    def test_error_files_still_counted_in_totals(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _write(tmp_path, "broken.py", "class :\n")

        knowledge = _build(scanner, tmp_path)

        assert knowledge.total_files == 1
        assert knowledge.parsed_files == []


class TestUnsupportedLanguages:
    def test_unsupported_language_files(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _write(tmp_path, "lib.rs", "fn main() {}\n")
        _write(tmp_path, "app.ts", "const x = 1;\n")

        knowledge = _build(scanner, tmp_path)

        for code_file in knowledge.files:
            assert code_file.parse_status is ParseStatus.UNSUPPORTED_LANGUAGE
            assert "No parser registered" in code_file.parse_message

    def test_serialization_round_trip(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _write(tmp_path, "app.py", "import os\n\ndef f():\n    pass\n")

        knowledge = _build(scanner, tmp_path)
        payload = knowledge.model_dump_json()
        restored = RepositoryKnowledge.model_validate_json(payload)

        assert restored.total_files == 1
        assert restored.files[0].symbols[0].name == "f"
        # Syntax trees are internal to parsers and never serialized.
        assert "tree" not in payload.lower()

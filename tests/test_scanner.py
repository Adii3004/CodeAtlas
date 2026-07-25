"""Unit tests for the repository scanner."""

from datetime import datetime
from pathlib import Path

import pytest

from scanner import (
    FileCategory,
    ProgrammingLanguage,
    RepositoryScanner,
    ScanError,
    ScanResult,
)


@pytest.fixture
def scanner() -> RepositoryScanner:
    return RepositoryScanner()


def _touch(path: Path, content: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


class TestEmptyRepository:
    def test_empty_directory_returns_no_files(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        result = scanner.scan(tmp_path)
        assert isinstance(result, ScanResult)
        assert result.total_files == 0
        assert result.total_size_bytes == 0
        assert result.files == []
        assert result.root_path == str(tmp_path.resolve())


class TestNestedFolders:
    def test_finds_files_in_nested_folders(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "top.py")
        _touch(tmp_path / "src" / "app.py")
        _touch(tmp_path / "src" / "deep" / "nested" / "module.py")

        result = scanner.scan(tmp_path)

        assert result.total_files == 3
        relative = [f.relative_path for f in result.files]
        assert relative == ["src/app.py", "src/deep/nested/module.py", "top.py"]

    def test_metadata_fields_are_populated(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "pkg" / "readme.MD", content="hello")

        [meta] = scanner.scan(tmp_path).files

        assert meta.filename == "readme.MD"
        assert meta.extension == ".md"  # normalized to lowercase
        assert meta.relative_path == "pkg/readme.MD"
        assert Path(meta.absolute_path).is_absolute()
        assert Path(meta.absolute_path).name == "readme.MD"
        assert meta.size_bytes == len("hello")
        assert isinstance(meta.last_modified, datetime)
        assert meta.category is FileCategory.DOCUMENTATION
        assert meta.language is ProgrammingLanguage.MARKDOWN

    def test_every_file_gets_a_category(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "app.py")
        _touch(tmp_path / "config.yaml")
        _touch(tmp_path / "mystery.xyz")

        result = scanner.scan(tmp_path)

        categories = {f.filename: f.category for f in result.files}
        assert categories == {
            "app.py": FileCategory.SOURCE_CODE,
            "config.yaml": FileCategory.CONFIGURATION,
            "mystery.xyz": FileCategory.UNKNOWN,
        }
        languages = {f.filename: f.language for f in result.files}
        assert languages == {
            "app.py": ProgrammingLanguage.PYTHON,
            "config.yaml": ProgrammingLanguage.YAML,
            "mystery.xyz": ProgrammingLanguage.UNKNOWN,
        }


class TestIgnoredFolders:
    @pytest.mark.parametrize(
        "folder",
        [
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            "build",
            "dist",
            ".idea",
            ".vscode",
        ],
    )
    def test_default_ignored_folder_is_skipped(
        self, scanner: RepositoryScanner, tmp_path: Path, folder: str
    ) -> None:
        _touch(tmp_path / "keep.py")
        _touch(tmp_path / folder / "inside.py")

        result = scanner.scan(tmp_path)

        assert [f.relative_path for f in result.files] == ["keep.py"]

    def test_ignored_folder_nested_deeper_is_skipped(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "src" / "node_modules" / "lib" / "index.js")
        _touch(tmp_path / "src" / "main.js")

        result = scanner.scan(tmp_path)

        assert [f.relative_path for f in result.files] == ["src/main.js"]

    def test_custom_ignored_dirs_override_defaults(self, tmp_path: Path) -> None:
        custom = RepositoryScanner(ignored_dirs={"secret"})
        _touch(tmp_path / "secret" / "hidden.py")
        _touch(tmp_path / "node_modules" / "lib.js")  # no longer ignored

        result = custom.scan(tmp_path)

        assert [f.relative_path for f in result.files] == ["node_modules/lib.js"]


class TestIgnoredFiles:
    @pytest.mark.parametrize("filename", ["module.pyc", "module.pyo", "app.log"])
    def test_default_ignored_file_is_skipped(
        self, scanner: RepositoryScanner, tmp_path: Path, filename: str
    ) -> None:
        _touch(tmp_path / "keep.py")
        _touch(tmp_path / filename)

        result = scanner.scan(tmp_path)

        assert [f.relative_path for f in result.files] == ["keep.py"]

    def test_similar_extensions_are_not_ignored(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "notes.logx")
        _touch(tmp_path / "script.py")

        result = scanner.scan(tmp_path)

        assert [f.relative_path for f in result.files] == ["notes.logx", "script.py"]


class TestInvalidPath:
    def test_nonexistent_path_raises_scan_error(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        with pytest.raises(ScanError, match="does not exist"):
            scanner.scan(tmp_path / "no_such_dir")

    def test_file_path_raises_scan_error(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        file_path = _touch(tmp_path / "a_file.txt")
        with pytest.raises(ScanError, match="not a directory"):
            scanner.scan(file_path)

"""Unit tests for the repository inventory."""

from pathlib import Path

import pytest

from scanner import (
    FileCategory,
    ProgrammingLanguage,
    RepositoryInventory,
    RepositoryScanner,
    build_inventory,
)


@pytest.fixture
def scanner() -> RepositoryScanner:
    return RepositoryScanner()


def _touch(path: Path, size: int = 1) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


class TestEmptyRepository:
    def test_empty_repository(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        inventory = build_inventory(scanner.scan(tmp_path))

        assert isinstance(inventory, RepositoryInventory)
        assert inventory.repository_name == tmp_path.resolve().name
        assert inventory.root_path == str(tmp_path.resolve())
        assert inventory.total_files == 0
        assert inventory.total_size_bytes == 0
        assert inventory.language_counts == {}
        assert inventory.extension_counts == {}
        assert inventory.largest_files == []
        assert inventory.largest_directories == []
        assert inventory.directory_stats == []
        # Category counts are zero-filled with stable keys.
        assert set(inventory.category_counts) == set(FileCategory)
        assert all(count == 0 for count in inventory.category_counts.values())


class TestSingleFile:
    def test_one_file(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        _touch(tmp_path / "app.py", size=42)

        inventory = build_inventory(scanner.scan(tmp_path))

        assert inventory.total_files == 1
        assert inventory.total_size_bytes == 42
        assert inventory.category_counts[FileCategory.SOURCE_CODE] == 1
        assert inventory.language_counts == {ProgrammingLanguage.PYTHON: 1}
        assert inventory.extension_counts == {".py": 1}
        assert [f.filename for f in inventory.largest_files] == ["app.py"]
        [root_stats] = inventory.directory_stats
        assert root_stats.path == "."
        assert root_stats.direct_file_count == 1
        assert root_stats.total_file_count == 1
        assert root_stats.total_size_bytes == 42


class TestNestedFolders:
    def test_directory_stats_are_cumulative(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "top.py", size=10)
        _touch(tmp_path / "src" / "a.py", size=20)
        _touch(tmp_path / "src" / "deep" / "b.py", size=30)
        _touch(tmp_path / "src" / "deep" / "c.py", size=40)

        inventory = build_inventory(scanner.scan(tmp_path))

        stats = {d.path: d for d in inventory.directory_stats}
        assert set(stats) == {".", "src", "src/deep"}

        assert stats["."].direct_file_count == 1
        assert stats["."].total_file_count == 4
        assert stats["."].total_size_bytes == 100

        assert stats["src"].direct_file_count == 1
        assert stats["src"].total_file_count == 3
        assert stats["src"].total_size_bytes == 90

        assert stats["src/deep"].direct_file_count == 2
        assert stats["src/deep"].total_file_count == 2
        assert stats["src/deep"].total_size_bytes == 70

    def test_largest_directories_ranked_by_direct_files(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        for i in range(3):
            _touch(tmp_path / "many" / f"f{i}.py")
        _touch(tmp_path / "few" / "single.py")

        inventory = build_inventory(scanner.scan(tmp_path))

        assert [d.path for d in inventory.largest_directories] == ["many", "few"]

    def test_largest_directories_limit(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        for i in range(5):
            _touch(tmp_path / f"dir{i}" / "file.py")

        inventory = build_inventory(scanner.scan(tmp_path), largest_directories_limit=2)

        assert len(inventory.largest_directories) == 2


class TestLargestFiles:
    def test_top_ten_by_size(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        for i in range(12):
            _touch(tmp_path / f"file{i:02d}.py", size=(i + 1) * 10)

        inventory = build_inventory(scanner.scan(tmp_path))

        assert len(inventory.largest_files) == 10
        sizes = [f.size_bytes for f in inventory.largest_files]
        assert sizes == sorted(sizes, reverse=True)
        assert sizes[0] == 120  # biggest file first
        assert inventory.largest_files[0].filename == "file11.py"

    def test_custom_limit(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        for i in range(5):
            _touch(tmp_path / f"f{i}.py", size=i + 1)

        inventory = build_inventory(scanner.scan(tmp_path), largest_files_limit=3)

        assert [f.size_bytes for f in inventory.largest_files] == [5, 4, 3]


class TestHomogeneousRepositories:
    def test_documentation_only(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "README.md")
        _touch(tmp_path / "docs" / "guide.md")
        _touch(tmp_path / "LICENSE")

        inventory = build_inventory(scanner.scan(tmp_path))

        assert inventory.category_counts[FileCategory.DOCUMENTATION] == 3
        assert inventory.category_counts[FileCategory.SOURCE_CODE] == 0
        assert inventory.language_counts == {
            ProgrammingLanguage.MARKDOWN: 2,
            ProgrammingLanguage.TEXT: 1,
        }
        assert inventory.extension_counts == {".md": 2, "(none)": 1}

    def test_source_code_only(self, scanner: RepositoryScanner, tmp_path: Path) -> None:
        _touch(tmp_path / "a.py")
        _touch(tmp_path / "b.py")
        _touch(tmp_path / "c.ts")

        inventory = build_inventory(scanner.scan(tmp_path))

        assert inventory.category_counts[FileCategory.SOURCE_CODE] == 3
        assert inventory.category_counts[FileCategory.DOCUMENTATION] == 0
        assert inventory.language_counts == {
            ProgrammingLanguage.PYTHON: 2,
            ProgrammingLanguage.TYPESCRIPT: 1,
        }
        assert inventory.extension_counts == {".py": 2, ".ts": 1}


class TestOrdering:
    def test_counts_ordered_by_frequency_then_name(
        self, scanner: RepositoryScanner, tmp_path: Path
    ) -> None:
        _touch(tmp_path / "a.py")
        _touch(tmp_path / "b.py")
        _touch(tmp_path / "x.md")
        _touch(tmp_path / "y.json")

        inventory = build_inventory(scanner.scan(tmp_path))

        assert list(inventory.extension_counts) == [".py", ".json", ".md"]
        assert list(inventory.language_counts) == [
            ProgrammingLanguage.PYTHON,
            ProgrammingLanguage.JSON,
            ProgrammingLanguage.MARKDOWN,
        ]

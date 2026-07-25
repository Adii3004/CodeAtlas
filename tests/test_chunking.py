"""Unit tests for the chunking engine."""

from pathlib import Path

from chunking import ChunkBuilder, ChunkType, RepositoryChunks
from knowledge import build_repository_knowledge
from scanner import RepositoryScanner


def _write(root: Path, name: str, content: str = "") -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _build(root: Path) -> RepositoryChunks:
    knowledge = build_repository_knowledge(RepositoryScanner().scan(root))
    return ChunkBuilder().build(knowledge)


class TestClassExtraction:
    def test_class_chunks(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "shapes.py",
            "class Circle:\n"
            "    def area(self):\n"
            "        return 3.14\n"
            "\n"
            "\n"
            "class Square:\n"
            "    side = 1\n",
        )

        chunks = _build(tmp_path)

        class_chunks = chunks.get_by_type(ChunkType.CLASS)
        assert [c.symbol_name for c in class_chunks] == ["Circle", "Square"]
        circle = class_chunks[0]
        assert circle.start_line == 1
        assert circle.end_line == 3
        assert "def area" in circle.content
        assert "class Square" not in circle.content
        assert circle.qualified_name == "Circle"
        assert circle.token_estimate > 0

    def test_file_summary_always_present(self, tmp_path: Path) -> None:
        _write(tmp_path, "one.py", "class One:\n    pass\n")

        chunks = _build(tmp_path)

        [summary] = chunks.get_by_type(ChunkType.FILE_SUMMARY)
        assert summary.relative_path == "one.py"
        assert "Classes: One" in summary.content
        assert "File: one.py" in summary.content


class TestFunctionExtraction:
    def test_function_chunks_including_async(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "tasks.py",
            "def sync_task():\n"
            "    return 1\n"
            "\n"
            "\n"
            "async def async_task():\n"
            "    return 2\n",
        )

        chunks = _build(tmp_path)

        function_chunks = chunks.get_by_type(ChunkType.FUNCTION)
        assert [c.symbol_name for c in function_chunks] == [
            "sync_task",
            "async_task",
        ]
        assert "async def async_task" in function_chunks[1].content
        # Symbols exist, so no MODULE chunk.
        assert chunks.get_by_type(ChunkType.MODULE) == []

    def test_imports_and_dependencies_recorded(self, tmp_path: Path) -> None:
        _write(tmp_path, "helper.py", "H = 1\n")
        _write(
            tmp_path,
            "app.py",
            "import os\nimport helper\n\ndef main():\n    pass\n",
        )

        chunks = _build(tmp_path)

        [chunk] = [
            c
            for c in chunks.get_by_type(ChunkType.FUNCTION)
            if c.relative_path == "app.py"
        ]
        assert chunk.imports == ["helper", "os"]
        assert chunk.dependencies == ["helper.py"]


class TestModuleFallback:
    def test_module_chunk_when_no_symbols(self, tmp_path: Path) -> None:
        _write(tmp_path, "constants.py", "A = 1\nB = 2\n")

        chunks = _build(tmp_path)

        [module_chunk] = chunks.get_by_type(ChunkType.MODULE)
        assert module_chunk.content == "A = 1\nB = 2"
        assert module_chunk.start_line == 1
        assert module_chunk.end_line == 2
        # FILE_SUMMARY still exists alongside.
        assert len(chunks.get_by_type(ChunkType.FILE_SUMMARY)) == 1

    def test_no_module_chunk_when_symbols_exist(self, tmp_path: Path) -> None:
        _write(tmp_path, "code.py", "X = 1\n\ndef f():\n    pass\n")

        chunks = _build(tmp_path)

        assert chunks.get_by_type(ChunkType.MODULE) == []


class TestMarkdownChunking:
    def test_readme_split_by_headings(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "README.md",
            "Intro text before headings.\n"
            "\n"
            "# Title\n"
            "Welcome.\n"
            "\n"
            "## Install\n"
            "pip install x\n"
            "\n"
            "## Usage\n"
            "Run it.\n",
        )

        chunks = _build(tmp_path)

        docs = chunks.get_by_type(ChunkType.DOCUMENTATION)
        assert [d.symbol_name for d in docs] == [
            None,  # preamble
            "Title",
            "Install",
            "Usage",
        ]
        install = docs[2]
        assert install.start_line == 6
        assert install.end_line == 8
        assert "pip install x" in install.content
        assert "Run it." not in install.content

    def test_markdown_without_headings_is_one_chunk(self, tmp_path: Path) -> None:
        _write(tmp_path, "notes.md", "just some notes\nwithout headings\n")

        chunks = _build(tmp_path)

        [doc] = chunks.get_by_type(ChunkType.DOCUMENTATION)
        assert doc.symbol_name is None
        assert doc.content == "just some notes\nwithout headings"

    def test_other_files_ignored(self, tmp_path: Path) -> None:
        _write(tmp_path, "data.json", '{"a": 1}\n')
        _write(tmp_path, "style.css", "body {}\n")

        chunks = _build(tmp_path)

        assert chunks.total_chunks == 0


class TestEmptyFiles:
    def test_empty_python_file(self, tmp_path: Path) -> None:
        _write(tmp_path, "empty.py", "")

        chunks = _build(tmp_path)

        # Summary only; no MODULE chunk for empty content.
        assert [c.chunk_type for c in chunks.chunks] == [ChunkType.FILE_SUMMARY]

    def test_empty_markdown_file(self, tmp_path: Path) -> None:
        _write(tmp_path, "empty.md", "")

        chunks = _build(tmp_path)

        assert chunks.total_chunks == 0

    def test_empty_repository(self, tmp_path: Path) -> None:
        chunks = _build(tmp_path)

        assert chunks.total_chunks == 0
        assert chunks.chunks == []


class TestDeterministicChunkIds:
    def test_ids_stable_across_builds(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.py", "def f():\n    pass\n")
        _write(tmp_path, "README.md", "# Title\ntext\n")

        first = _build(tmp_path)
        second = _build(tmp_path)

        assert [c.chunk_id for c in first.chunks] == [c.chunk_id for c in second.chunks]

    def test_ids_unique_within_repository(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "mod.py",
            "class A:\n    pass\n\nclass B:\n    pass\n\ndef f():\n    pass\n",
        )
        _write(tmp_path, "README.md", "# One\nx\n# Two\ny\n")

        chunks = _build(tmp_path)

        ids = [c.chunk_id for c in chunks.chunks]
        assert len(ids) == len(set(ids))

    def test_helpers(self, tmp_path: Path) -> None:
        _write(tmp_path, "x.py", "def f():\n    pass\n")
        _write(tmp_path, "y.py", "Y = 1\n")

        chunks = _build(tmp_path)

        assert len(chunks.get_chunks_for_file("x.py")) == 2  # summary + function
        assert chunks.get_chunks_for_file("missing.py") == []

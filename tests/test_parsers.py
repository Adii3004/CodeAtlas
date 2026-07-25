"""Unit tests for the parser framework."""

from datetime import datetime
from typing import ClassVar

import pytest

from parsers import (
    BaseParser,
    ParseResult,
    ParserManager,
    ParseStatus,
    PythonParser,
    create_default_manager,
)
from scanner import FileCategory, FileMetadata, ProgrammingLanguage


def _metadata(
    relative_path: str = "src/app.py",
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
) -> FileMetadata:
    return FileMetadata(
        absolute_path=f"C:/repo/{relative_path}",
        relative_path=relative_path,
        filename=relative_path.rsplit("/", 1)[-1],
        extension="." + relative_path.rsplit(".", 1)[-1]
        if "." in relative_path
        else "",
        size_bytes=100,
        last_modified=datetime(2026, 7, 25, 12, 0, 0),
        category=FileCategory.SOURCE_CODE,
        language=language,
    )


class TestParserSelection:
    def test_manager_selects_python_parser(self) -> None:
        manager = create_default_manager()
        parser = manager.get_parser(ProgrammingLanguage.PYTHON)
        assert isinstance(parser, PythonParser)

    def test_supported_languages(self) -> None:
        manager = create_default_manager()
        assert manager.supported_languages == {ProgrammingLanguage.PYTHON}

    def test_dispatch_uses_file_language(self) -> None:
        # Nonexistent path: the Python parser runs and reports a read error,
        # proving dispatch reached the right parser without raising.
        manager = create_default_manager()
        result = manager.parse(_metadata("src/app.py"))
        assert result.language is ProgrammingLanguage.PYTHON
        assert result.status is ParseStatus.ERROR
        assert "Cannot read file" in result.message

    def test_custom_parser_registration(self) -> None:
        class GoParser(BaseParser):
            language: ClassVar[ProgrammingLanguage] = ProgrammingLanguage.GO

            def parse(self, file_metadata: FileMetadata) -> ParseResult:
                return ParseResult(
                    file_path=file_metadata.relative_path,
                    language=self.language,
                    status=ParseStatus.SUCCESS,
                )

        manager = ParserManager()
        manager.register(GoParser())

        result = manager.parse(_metadata("main.go", ProgrammingLanguage.GO))
        assert result.status is ParseStatus.SUCCESS
        assert result.ok

    def test_reregistration_replaces_parser(self) -> None:
        manager = create_default_manager()
        replacement = PythonParser()
        manager.register(replacement)
        assert manager.get_parser(ProgrammingLanguage.PYTHON) is replacement


class TestUnsupportedLanguages:
    @pytest.mark.parametrize(
        "language",
        [
            ProgrammingLanguage.RUST,
            ProgrammingLanguage.MARKDOWN,
            ProgrammingLanguage.UNKNOWN,
        ],
    )
    def test_unsupported_language_does_not_raise(
        self, language: ProgrammingLanguage
    ) -> None:
        manager = create_default_manager()
        result = manager.parse(_metadata("some/file.x", language))

        assert result.status is ParseStatus.UNSUPPORTED_LANGUAGE
        assert result.language is language
        assert language.value in result.message
        assert not result.ok

    def test_get_parser_returns_none_for_unsupported(self) -> None:
        manager = create_default_manager()
        assert manager.get_parser(ProgrammingLanguage.RUST) is None


class TestPythonParserViaManager:
    def test_result_shape(self) -> None:
        result = PythonParser().parse(_metadata("pkg/module.py"))

        assert result.file_path == "pkg/module.py"
        assert result.language is ProgrammingLanguage.PYTHON
        assert result.symbols == []

    def test_parser_never_raises_for_bad_paths(self) -> None:
        parser = PythonParser()
        for path in ("a.py", "weird name.py", "no_extension"):
            result = parser.parse(_metadata(path))
            assert isinstance(result, ParseResult)
            assert result.status is ParseStatus.ERROR


class TestManagerErrorHandling:
    def test_raising_parser_is_converted_to_error_result(self) -> None:
        class BrokenParser(BaseParser):
            language: ClassVar[ProgrammingLanguage] = ProgrammingLanguage.PYTHON

            def parse(self, file_metadata: FileMetadata) -> ParseResult:
                raise RuntimeError("boom")

        manager = ParserManager()
        manager.register(BrokenParser())

        result = manager.parse(_metadata())

        assert result.status is ParseStatus.ERROR
        assert "boom" in result.message

    def test_base_parser_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            BaseParser()  # type: ignore[abstract]

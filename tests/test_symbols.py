"""Unit tests for top-level symbol extraction."""

import tree_sitter_python
from tree_sitter import Language, Parser, Tree

from parsers import Symbol, SymbolType, extract_top_level_symbols

_PARSER = Parser(Language(tree_sitter_python.language()))


def _parse(source: str) -> Tree:
    return _PARSER.parse(source.encode("utf-8"))


def _extract(source: str, path: str = "pkg/module.py") -> list[Symbol]:
    return extract_top_level_symbols(_parse(source), path)


class TestClasses:
    def test_multiple_classes(self) -> None:
        symbols = _extract(
            "class First:\n"
            "    pass\n"
            "\n"
            "class Second:\n"
            "    pass\n"
            "\n"
            "class Third:\n"
            "    pass\n"
        )

        assert [s.name for s in symbols] == ["First", "Second", "Third"]
        assert all(s.symbol_type is SymbolType.CLASS for s in symbols)

    def test_class_positions(self) -> None:
        [symbol] = _extract("class Alone:\n    x = 1\n    y = 2\n")

        assert symbol.start_line == 1
        assert symbol.end_line == 3
        assert symbol.start_column == 1
        assert symbol.file_path == "pkg/module.py"

    def test_qualified_name_currently_equals_name(self) -> None:
        symbols = _extract("class A:\n    pass\n\ndef f():\n    pass\n")

        assert all(s.qualified_name == s.name for s in symbols)


class TestFunctions:
    def test_multiple_functions(self) -> None:
        symbols = _extract(
            "def alpha():\n    pass\n\n"
            "def beta(x, y):\n    return x + y\n\n"
            "def gamma():\n    pass\n"
        )

        assert [s.name for s in symbols] == ["alpha", "beta", "gamma"]
        assert all(s.symbol_type is SymbolType.FUNCTION for s in symbols)

    def test_function_positions(self) -> None:
        symbols = _extract("x = 1\n\ndef later():\n    return 42\n")

        [symbol] = symbols
        assert symbol.name == "later"
        assert symbol.start_line == 3
        assert symbol.end_line == 4


class TestAsyncFunctions:
    def test_async_function(self) -> None:
        [symbol] = _extract("async def fetch(url):\n    return url\n")

        assert symbol.name == "fetch"
        assert symbol.symbol_type is SymbolType.ASYNC_FUNCTION

    def test_mixed_sync_and_async(self) -> None:
        symbols = _extract(
            "def sync_one():\n    pass\n\nasync def async_one():\n    pass\n"
        )

        assert [(s.name, s.symbol_type) for s in symbols] == [
            ("sync_one", SymbolType.FUNCTION),
            ("async_one", SymbolType.ASYNC_FUNCTION),
        ]


class TestEmptyAndComments:
    def test_empty_file(self) -> None:
        assert _extract("") == []

    def test_comments_only(self) -> None:
        assert _extract("# a comment\n# another\n") == []

    def test_module_with_only_statements(self) -> None:
        assert _extract("x = 1\nprint(x)\n") == []


class TestExclusions:
    def test_nested_functions_not_extracted(self) -> None:
        symbols = _extract(
            "def outer():\n    def inner():\n        pass\n    return inner\n"
        )

        assert [s.name for s in symbols] == ["outer"]

    def test_methods_not_extracted(self) -> None:
        symbols = _extract(
            "class Service:\n"
            "    def method_one(self):\n"
            "        pass\n"
            "\n"
            "    async def method_two(self):\n"
            "        pass\n"
        )

        assert [s.name for s in symbols] == ["Service"]
        assert symbols[0].symbol_type is SymbolType.CLASS

    def test_class_inside_function_not_extracted(self) -> None:
        symbols = _extract(
            "def factory():\n    class Local:\n        pass\n    return Local\n"
        )

        assert [s.name for s in symbols] == ["factory"]


class TestDecoratedDefinitions:
    def test_decorated_function_is_extracted_without_decorator_info(self) -> None:
        [symbol] = _extract("@lru_cache\ndef cached():\n    return 1\n")

        assert symbol.name == "cached"
        assert symbol.symbol_type is SymbolType.FUNCTION

    def test_decorated_class_and_async(self) -> None:
        symbols = _extract(
            "@register\nclass Plugin:\n    pass\n\n"
            "@retry\nasync def poll():\n    pass\n"
        )

        assert [(s.name, s.symbol_type) for s in symbols] == [
            ("Plugin", SymbolType.CLASS),
            ("poll", SymbolType.ASYNC_FUNCTION),
        ]


class TestUnicodeNames:
    def test_unicode_symbol_names(self) -> None:
        [symbol] = _extract("def größe():\n    pass\n")

        assert symbol.name == "größe"

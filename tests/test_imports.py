"""Unit tests for import extraction."""

import tree_sitter_python
from tree_sitter import Language, Parser, Tree

from parsers import Import, extract_imports

_PARSER = Parser(Language(tree_sitter_python.language()))


def _extract(source: str, path: str = "pkg/module.py") -> list[Import]:
    tree: Tree = _PARSER.parse(source.encode("utf-8"))
    return extract_imports(tree, path)


class TestSimpleImports:
    def test_single_import(self) -> None:
        [imp] = _extract("import os\n")

        assert imp.module == "os"
        assert imp.name is None
        assert imp.alias is None
        assert imp.relative_level == 0
        assert imp.line == 1
        assert imp.file_path == "pkg/module.py"

    def test_dotted_module(self) -> None:
        [imp] = _extract("import a.b.c\n")

        assert imp.module == "a.b.c"

    def test_line_numbers(self) -> None:
        imports = _extract("import os\n\nimport sys\n")

        assert [(i.module, i.line) for i in imports] == [("os", 1), ("sys", 3)]


class TestAliases:
    def test_import_as(self) -> None:
        [imp] = _extract("import numpy as np\n")

        assert imp.module == "numpy"
        assert imp.alias == "np"
        assert imp.name is None

    def test_from_import_as(self) -> None:
        [imp] = _extract("from typing import List as L\n")

        assert imp.module == "typing"
        assert imp.name == "List"
        assert imp.alias == "L"


class TestFromImports:
    def test_single_name(self) -> None:
        [imp] = _extract("from pathlib import Path\n")

        assert imp.module == "pathlib"
        assert imp.name == "Path"
        assert imp.relative_level == 0

    def test_multiple_names_one_line(self) -> None:
        imports = _extract("from typing import List, Optional, Union\n")

        assert [(i.module, i.name) for i in imports] == [
            ("typing", "List"),
            ("typing", "Optional"),
            ("typing", "Union"),
        ]

    def test_mixed_alias_and_plain_names(self) -> None:
        imports = _extract("from typing import List as L, Optional\n")

        assert [(i.name, i.alias) for i in imports] == [
            ("List", "L"),
            ("Optional", None),
        ]

    def test_parenthesized_multiline(self) -> None:
        imports = _extract(
            "from collections import (\n    Counter,\n    defaultdict,\n)\n"
        )

        assert [(i.name, i.line) for i in imports] == [
            ("Counter", 2),
            ("defaultdict", 3),
        ]


class TestWildcardImports:
    def test_wildcard(self) -> None:
        [imp] = _extract("from x import *\n")

        assert imp.module == "x"
        assert imp.name == "*"
        assert imp.is_wildcard

    def test_non_wildcard_is_not_flagged(self) -> None:
        [imp] = _extract("from x import y\n")

        assert not imp.is_wildcard


class TestRelativeImports:
    def test_single_dot_no_module(self) -> None:
        [imp] = _extract("from . import models\n")

        assert imp.module is None
        assert imp.name == "models"
        assert imp.relative_level == 1

    def test_double_dot_with_module(self) -> None:
        [imp] = _extract("from ..pkg.sub import thing\n")

        assert imp.module == "pkg.sub"
        assert imp.name == "thing"
        assert imp.relative_level == 2

    def test_triple_dot(self) -> None:
        [imp] = _extract("from ... import far\n")

        assert imp.module is None
        assert imp.relative_level == 3

    def test_relative_wildcard(self) -> None:
        [imp] = _extract("from .local import *\n")

        assert imp.module == "local"
        assert imp.relative_level == 1
        assert imp.is_wildcard


class TestMultipleImportsOneLine:
    def test_comma_separated_import(self) -> None:
        imports = _extract("import os, sys, json\n")

        assert [i.module for i in imports] == ["os", "sys", "json"]
        assert all(i.line == 1 for i in imports)

    def test_comma_separated_with_alias(self) -> None:
        imports = _extract("import os, numpy as np\n")

        assert [(i.module, i.alias) for i in imports] == [
            ("os", None),
            ("numpy", "np"),
        ]


class TestEmptyAndComments:
    def test_empty_file(self) -> None:
        assert _extract("") == []

    def test_comments_only(self) -> None:
        assert _extract("# import os\n# from x import y\n") == []

    def test_import_in_string_not_extracted(self) -> None:
        assert _extract("s = 'import os'\n") == []


class TestNestedImports:
    def test_import_inside_function_is_extracted(self) -> None:
        [imp] = _extract("def lazy():\n    import json\n    return json\n")

        assert imp.module == "json"
        assert imp.line == 2

    def test_ordering_is_by_line(self) -> None:
        imports = _extract("import zlib\n\ndef f():\n    import abc\n\nimport os\n")

        assert [i.module for i in imports] == ["zlib", "abc", "os"]

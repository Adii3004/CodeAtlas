"""Top-level symbol extraction from Tree-sitter syntax trees.

Extracts only top-level classes, functions, and async functions. Nested
functions, methods, imports, variables, decorators, inheritance, and
docstrings are deliberately out of scope for this milestone.
"""

import logging
from enum import StrEnum

from pydantic import BaseModel
from tree_sitter import Node, Tree

logger = logging.getLogger(__name__)


class SymbolType(StrEnum):
    """Kind of extracted symbol."""

    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"


class Symbol(BaseModel):
    """One top-level symbol found in a source file.

    Lines and columns are 1-based; ``end_line``/``end_column`` point at the
    end of the definition (including its body). ``qualified_name`` is
    currently identical to ``name``; once namespace/module resolution lands
    it will carry the dotted path (e.g. ``utils.helpers.calculate``).
    """

    name: str
    qualified_name: str
    symbol_type: SymbolType
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    file_path: str


_DEFINITION_TYPES: frozenset[str] = frozenset(
    {"class_definition", "function_definition"}
)


def extract_top_level_symbols(tree: Tree, relative_path: str) -> list[Symbol]:
    """Extract top-level class/function symbols from a parsed module.

    Only direct children of the module node are considered — nothing inside
    a class or function body is visited, which is what keeps methods and
    nested functions out. A top-level ``decorated_definition`` contributes
    the definition it wraps (the decorator itself is ignored).
    """
    symbols: list[Symbol] = []
    for child in tree.root_node.named_children:
        node = child
        if node.type == "decorated_definition":
            definition = node.child_by_field_name("definition")
            if definition is None:
                continue
            node = definition
        if node.type not in _DEFINITION_TYPES:
            continue
        symbol = _build_symbol(node, relative_path)
        if symbol is not None:
            symbols.append(symbol)
    logger.debug("Extracted %d top-level symbols from %s", len(symbols), relative_path)
    return symbols


def _build_symbol(node: Node, relative_path: str) -> Symbol | None:
    """Build a Symbol from a class_definition or function_definition node."""
    name_node = node.child_by_field_name("name")
    if name_node is None or name_node.text is None:
        logger.debug("Skipping unnamed definition node in %s", relative_path)
        return None

    if node.type == "class_definition":
        symbol_type = SymbolType.CLASS
    elif any(child.type == "async" for child in node.children):
        symbol_type = SymbolType.ASYNC_FUNCTION
    else:
        symbol_type = SymbolType.FUNCTION

    name = name_node.text.decode("utf-8")
    return Symbol(
        name=name,
        qualified_name=name,
        symbol_type=symbol_type,
        start_line=node.start_point.row + 1,
        end_line=node.end_point.row + 1,
        start_column=node.start_point.column + 1,
        end_column=node.end_point.column + 1,
        file_path=relative_path,
    )

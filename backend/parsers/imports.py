"""Import extraction from Tree-sitter syntax trees.

Extracts every ``import`` and ``from ... import`` statement in a module,
including imports nested inside functions or classes. Nothing else —
variables, calls, decorators, and comments are out of scope.
"""

import logging
from enum import StrEnum

from pydantic import BaseModel
from tree_sitter import Node, Tree

logger = logging.getLogger(__name__)

WILDCARD = "*"


class Import(BaseModel):
    """One imported binding.

    Every ``from`` target gets its own entry: ``from x import a, b`` yields
    two Imports. Semantics by statement form:

    - ``import os``               → module="os", name=None
    - ``import numpy as np``      → module="numpy", name=None, alias="np"
    - ``from pathlib import Path``→ module="pathlib", name="Path"
    - ``from x import *``         → module="x", name="*"
    - ``from . import models``    → module=None, name="models", relative_level=1
    - ``from ..pkg import thing`` → module="pkg", name="thing", relative_level=2
    """

    module: str | None
    name: str | None = None
    alias: str | None = None
    relative_level: int = 0
    line: int
    file_path: str

    @property
    def is_wildcard(self) -> bool:
        """True for ``from module import *``."""
        return self.name == WILDCARD


class _StatementType(StrEnum):
    IMPORT = "import_statement"
    IMPORT_FROM = "import_from_statement"


def extract_imports(tree: Tree, relative_path: str) -> list[Import]:
    """Extract all import statements from a parsed Python module."""
    imports: list[Import] = []
    stack: list[Node] = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == _StatementType.IMPORT:
            imports.extend(_from_import_statement(node, relative_path))
        elif node.type == _StatementType.IMPORT_FROM:
            imports.extend(_from_import_from_statement(node, relative_path))
        else:
            stack.extend(reversed(node.named_children))
    imports.sort(key=lambda imp: imp.line)
    logger.debug("Extracted %d imports from %s", len(imports), relative_path)
    return imports


def _from_import_statement(node: Node, relative_path: str) -> list[Import]:
    """Handle ``import a.b.c, json`` and ``import numpy as np``."""
    imports: list[Import] = []
    for entry in node.children_by_field_name("name"):
        module, alias = _module_and_alias(entry)
        if module is None:
            continue
        imports.append(
            Import(
                module=module,
                alias=alias,
                line=entry.start_point.row + 1,
                file_path=relative_path,
            )
        )
    return imports


def _from_import_from_statement(node: Node, relative_path: str) -> list[Import]:
    """Handle ``from module import ...`` in all its forms."""
    module, level = _resolve_module(node.child_by_field_name("module_name"))

    if any(child.type == "wildcard_import" for child in node.children):
        return [
            Import(
                module=module,
                name=WILDCARD,
                relative_level=level,
                line=node.start_point.row + 1,
                file_path=relative_path,
            )
        ]

    imports: list[Import] = []
    for entry in node.children_by_field_name("name"):
        name, alias = _module_and_alias(entry)
        if name is None:
            continue
        imports.append(
            Import(
                module=module,
                name=name,
                alias=alias,
                relative_level=level,
                line=entry.start_point.row + 1,
                file_path=relative_path,
            )
        )
    return imports


def _module_and_alias(entry: Node) -> tuple[str | None, str | None]:
    """Decode a dotted_name or aliased_import node into (text, alias)."""
    if entry.type == "aliased_import":
        name_node = entry.child_by_field_name("name")
        alias_node = entry.child_by_field_name("alias")
        name = name_node.text.decode("utf-8") if name_node and name_node.text else None
        alias = (
            alias_node.text.decode("utf-8") if alias_node and alias_node.text else None
        )
        return name, alias
    if entry.text is None:
        return None, None
    return entry.text.decode("utf-8"), None


def _resolve_module(module_node: Node | None) -> tuple[str | None, int]:
    """Return (module, relative_level) for a from-import's module node.

    Absolute imports have level 0; ``from .`` / ``from ..pkg`` count their
    leading dots. ``from . import x`` has no module at all → (None, 1).
    """
    if module_node is None:
        return None, 0
    if module_node.type == "relative_import":
        text = module_node.text.decode("utf-8") if module_node.text else ""
        level = len(text) - len(text.lstrip("."))
        remainder = text.lstrip(".")
        return (remainder or None), level
    return (module_node.text.decode("utf-8") if module_node.text else None), 0

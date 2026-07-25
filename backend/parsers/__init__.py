"""Parser framework: language-dispatched parsing behind one common interface.

No parser reads file contents yet — this package defines the architecture
that future Tree-sitter-based parsers will plug into.
"""

from parsers.base import BaseParser
from parsers.imports import Import, extract_imports
from parsers.manager import ParserManager, create_default_manager
from parsers.models import ParseResult, ParseStatus
from parsers.python_parser import PythonParser
from parsers.symbols import Symbol, SymbolType, extract_top_level_symbols

__all__ = [
    "BaseParser",
    "Import",
    "ParseResult",
    "ParseStatus",
    "ParserManager",
    "PythonParser",
    "Symbol",
    "SymbolType",
    "create_default_manager",
    "extract_imports",
    "extract_top_level_symbols",
]

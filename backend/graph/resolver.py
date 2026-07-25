"""Module resolver: maps Python imports to files inside the repository.

Standard-library imports are recognized and skipped; anything else that
cannot be mapped to a repository file is reported as unresolved (which,
for now, includes third-party packages — future diagnostics can split
those out).
"""

import logging
import sys
from pathlib import PurePosixPath

from knowledge.models import CodeFile
from parsers.imports import WILDCARD, Import
from scanner.language import ProgrammingLanguage

logger = logging.getLogger(__name__)

_STDLIB_MODULES: frozenset[str] = frozenset(sys.stdlib_module_names)


class ModuleResolver:
    """Resolves absolute and relative imports to repository file paths.

    The index maps dotted module paths (rooted at the repository root) to
    relative file paths: ``backend/scanner/models.py`` indexes as
    ``backend.scanner.models`` and ``backend/scanner/__init__.py`` as
    ``backend.scanner``.

    Because source code often imports relative to a nested package root
    (e.g. ``from scanner.models import ...`` with ``backend/`` on
    ``sys.path``), absolute lookups also match dotted suffixes; ties pick
    the shallowest, then alphabetically first, candidate.
    """

    def __init__(self, code_files: list[CodeFile]) -> None:
        self._by_dotted: dict[str, str] = {}
        for code_file in code_files:
            if code_file.language is not ProgrammingLanguage.PYTHON:
                continue
            parts = PurePosixPath(code_file.relative_path).with_suffix("").parts
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            if not parts:
                continue
            self._by_dotted[".".join(parts)] = code_file.relative_path

    def resolve(self, source_path: str, imp: Import) -> str | None:
        """Return the repository-relative path an import refers to, or None."""
        if imp.relative_level > 0:
            return self._resolve_relative(source_path, imp)
        return self._resolve_absolute(imp)

    @staticmethod
    def is_standard_library(imp: Import) -> bool:
        """True if the import targets the Python standard library."""
        if imp.relative_level > 0 or imp.module is None:
            return False
        return imp.module.split(".", 1)[0] in _STDLIB_MODULES

    def _resolve_absolute(self, imp: Import) -> str | None:
        if imp.module is None:
            return None
        candidates: list[str] = []
        if imp.name and imp.name != WILDCARD:
            # `from pkg import sub` may target the submodule pkg/sub.py.
            candidates.append(f"{imp.module}.{imp.name}")
        # `import a.b.c` depends on a/b/c.py, or failing that a parent package.
        module_parts = imp.module.split(".")
        candidates.extend(
            ".".join(module_parts[:i]) for i in range(len(module_parts), 0, -1)
        )
        for candidate in candidates:
            resolved = self._lookup(candidate)
            if resolved is not None:
                return resolved
        return None

    def _resolve_relative(self, source_path: str, imp: Import) -> str | None:
        package_parts = list(PurePosixPath(source_path).parts[:-1])
        ascend = imp.relative_level - 1
        if ascend > len(package_parts):
            return None  # points above the repository root
        base = package_parts[: len(package_parts) - ascend] if ascend else package_parts

        candidates: list[list[str]] = []
        module_parts = imp.module.split(".") if imp.module else []
        if imp.name and imp.name != WILDCARD:
            candidates.append(base + module_parts + [imp.name])
        if module_parts:
            candidates.append(base + module_parts)
        elif base:
            candidates.append(base)

        for parts in candidates:
            if not parts:
                continue
            # Relative candidates are anchored at the repo root: exact only.
            resolved = self._by_dotted.get(".".join(parts))
            if resolved is not None:
                return resolved
        return None

    def _lookup(self, dotted: str) -> str | None:
        exact = self._by_dotted.get(dotted)
        if exact is not None:
            return exact
        suffix = "." + dotted
        matches = [d for d in self._by_dotted if d.endswith(suffix)]
        if not matches:
            return None
        best = min(matches, key=lambda d: (d.count("."), d))
        if len(matches) > 1:
            logger.debug(
                "Ambiguous module %r: %d candidates, picked %s",
                dotted,
                len(matches),
                best,
            )
        return self._by_dotted[best]

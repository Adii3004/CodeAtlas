"""Example: scan a local repository and print discovered file metadata.

Usage (from the project root):

    backend\\venv\\Scripts\\python.exe examples\\scan_repository.py [path]

If no path is given, the CodeAtlas project itself is scanned.
"""

import sys
from pathlib import Path

# Make the backend packages importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from scanner import RepositoryScanner, ScanError  # noqa: E402
from utils.logging import configure_logging  # noqa: E402


def main() -> int:
    configure_logging("INFO")
    target = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    )

    scanner = RepositoryScanner()
    try:
        result = scanner.scan(target)
    except ScanError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"\nRepository: {result.root_path}")
    print(f"Files found: {result.total_files}")
    print(f"Total size:  {result.total_size_bytes:,} bytes\n")

    for meta in result.files[:20]:
        print(
            f"  {meta.relative_path:<50} {meta.category.value:<14} "
            f"{meta.language.value:<11} "
            f"{meta.size_bytes:>10,} B  {meta.last_modified:%Y-%m-%d %H:%M}"
        )
    if result.total_files > 20:
        print(f"  ... and {result.total_files - 20} more files")

    def print_counts(title: str, values: list[str]) -> None:
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        print(f"\n{title}:")
        for value, count in sorted(counts.items(), key=lambda item: -item[1]):
            print(f"  {value:<14} {count:>4}")

    print_counts("Files per category", [m.category.value for m in result.files])
    print_counts("Files per language", [m.language.value for m in result.files])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

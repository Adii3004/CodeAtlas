"""Example: build and print a repository inventory.

Usage (from the project root):

    backend\\venv\\Scripts\\python.exe examples\\repository_inventory.py [path]

If no path is given, the CodeAtlas project itself is inventoried.
"""

import sys
from pathlib import Path

# Make the backend packages importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from scanner import RepositoryScanner, ScanError, build_inventory  # noqa: E402
from utils.logging import configure_logging  # noqa: E402


def main() -> int:
    configure_logging("WARNING")
    target = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    )

    try:
        scan_result = RepositoryScanner().scan(target)
    except ScanError as exc:
        print(f"Error: {exc}")
        return 1
    inventory = build_inventory(scan_result)

    print(f"Repository: {inventory.repository_name}")
    print(f"Root:       {inventory.root_path}")
    print(f"Files:      {inventory.total_files}")
    print(f"Size:       {inventory.total_size_bytes:,} bytes")

    print("\nCategories:")
    for category, count in inventory.category_counts.items():
        if count:
            print(f"  {category.value:<14} {count:>4}")

    print("\nLanguages:")
    for language, count in inventory.language_counts.items():
        print(f"  {language.value:<14} {count:>4}")

    print("\nExtensions:")
    for extension, count in inventory.extension_counts.items():
        print(f"  {extension:<14} {count:>4}")

    print("\nLargest files:")
    for meta in inventory.largest_files:
        print(f"  {meta.relative_path:<50} {meta.size_bytes:>10,} B")

    print("\nLargest directories (by direct file count):")
    for stats in inventory.largest_directories:
        print(
            f"  {stats.path:<40} direct={stats.direct_file_count:<4} "
            f"total={stats.total_file_count:<4} {stats.total_size_bytes:>10,} B"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

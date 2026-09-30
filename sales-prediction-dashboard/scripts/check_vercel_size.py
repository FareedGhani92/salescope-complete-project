"""Check built Vercel function bundles against the project's 225 MB budget."""

from __future__ import annotations

import sys
from pathlib import Path


LIMIT_BYTES = 225_000_000  # Decimal MB, keeping the check conservative.
FUNCTIONS_DIR = Path(".vercel/output/functions")


def directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> int:
    functions = sorted(FUNCTIONS_DIR.glob("*.func"))
    if not functions:
        print("No built Vercel functions found. Run `vercel build` first.", file=sys.stderr)
        return 2

    failed = False
    for function in functions:
        size = directory_size(function)
        size_mb = size / 1_000_000
        print(f"{function.name}: {size_mb:.1f} MB / 225 MB")
        if size > LIMIT_BYTES:
            failed = True

    if failed:
        print("At least one function exceeds the 225 MB deployment budget.", file=sys.stderr)
        return 1

    print("All built function bundles are within the 225 MB deployment budget.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

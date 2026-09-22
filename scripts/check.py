"""Quality gate = Definition of Done. Runs lint (ruff) and all tests (architecture + unit).

Usage:
    python scripts/check.py          # must print "ALL CHECKS PASSED" before a task is finished
    python scripts/check.py --fix    # auto-fix lint/format issues first
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(title: str, command: list[str]) -> bool:
    print(f"\n=== {title} ===", flush=True)
    # UTF-8 mode: Vietnamese messages must not crash on Windows consoles (cp1252)
    result = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    print(f"--> {'OK' if result.returncode == 0 else 'FAILED'}", flush=True)
    return result.returncode == 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="run ruff --fix and ruff format first")
    args = parser.parse_args()
    python = sys.executable
    if args.fix:
        run("Auto-fix (ruff)", [python, "-m", "ruff", "check", ".", "--fix"])
        run("Format (ruff)", [python, "-m", "ruff", "format", "."])
    results = [
        run("Lint (ruff)", [python, "-m", "ruff", "check", "."]),
        run("Tests: architecture + features (pytest)", [python, "-m", "pytest"]),
    ]
    if all(results):
        print("\nALL CHECKS PASSED")
        return 0
    print(
        "\nCHECKS FAILED - fix the errors above (never weaken or skip tests). See docs/rules/07-testing-and-verification.md"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

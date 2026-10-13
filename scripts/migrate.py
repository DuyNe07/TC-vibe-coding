"""Database migrations (Alembic, backend/core/migrate.py). Uses the database of .env, like the app.

Usage:
    python scripts/migrate.py                              # apply every pending revision (run.ps1 / Docker do it)
    python scripts/migrate.py status                       # list chains that still have pending revisions
    python scripts/migrate.py new <feature_key|core> "..."  # create the next empty revision file to fill in
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core import migrate  # noqa: E402


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    action = argv[0] if argv else "upgrade"
    if action == "upgrade":
        moved = migrate.upgrade()
        print("\n".join(moved) if moved else "Database is up to date")
        return 0
    if action == "status":
        waiting = migrate.pending()
        for name, change in waiting.items():
            print(f"PENDING {name}: {change}")
        print("Database is up to date" if not waiting else "Run: python scripts/migrate.py")
        return 1 if waiting else 0
    if action == "new" and len(argv) == 3:
        print(f"Created {migrate.new_revision(argv[1], argv[2])}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

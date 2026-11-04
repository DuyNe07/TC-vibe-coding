"""SUPREME-RULES.md, data safety: features never hard-delete stored data (soft delete only) and never talk SQL."""

import ast
import re

import pytest

from tests.architecture.helpers import BACKEND_FEATURES, FRONTEND_FEATURES, feature_keys, imports_of, python_files, rel

KEYS = feature_keys(BACKEND_FEATURES)
# private repository internals that bypass the delete flag, and raw SQL that destroys rows
FORBIDDEN_CALLS = {"_purge", "_write", "_save", "_stored"}
FORBIDDEN_SQL = re.compile(r"\b(DELETE\s+FROM|TRUNCATE|DROP\s+TABLE)\b", re.IGNORECASE)


def _feature_files(key: str) -> list:
    files = [*python_files(BACKEND_FEATURES / key), *python_files(FRONTEND_FEATURES / key)]
    return [f for f in files if "migrations" not in f.parts and "tests" not in f.parts]


@pytest.mark.parametrize("key", KEYS)
def test_features_only_soft_delete(key: str) -> None:
    problems = []
    for path in _feature_files(key):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            internal = isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_CALLS
            via_super = internal and isinstance(node.value, ast.Call) and getattr(node.value.func, "id", "") == "super"
            if internal and not via_super:
                problems.append(f"{rel(path)}:{node.lineno} uses repository internal .{node.attr}")
        if FORBIDDEN_SQL.search(source):
            problems.append(f"{rel(path)}: raw SQL that destroys rows")
        problems += [
            f"{rel(path)}:{ref.lineno} imports {ref.module}"
            for ref in imports_of(path)
            if ref.module.split(".")[0] in {"sqlalchemy", "sqlite3", "asyncpg", "psycopg", "psycopg2"}
            or ref.module == "backend.core.db"
        ]
    assert not problems, (
        "Stored data is never destroyed (SUPREME-RULES.md): delete with repository.delete() (sets the delete flag), "
        "restore with repository.restore(). Problems:\n" + "\n".join(problems)
    )

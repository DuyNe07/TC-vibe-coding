"""Shared helpers for architecture tests (AST parsing, feature discovery)."""

import ast
import importlib
import inspect
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
BACKEND_FEATURES = BACKEND / "features"
FRONTEND_FEATURES = FRONTEND / "features"
BUSINESS_DOCS = ROOT / "docs" / "business"


def feature_keys(base: Path) -> list[str]:
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def python_files(base: Path) -> Iterator[Path]:
    for path in sorted(base.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


@dataclass(frozen=True)
class ImportRef:
    lineno: int
    module: str
    names: tuple[str, ...]


def imports_of(path: Path) -> list[ImportRef]:
    """Absolute module names imported by a file (relative imports resolved)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = module_name(path) if path.name == "__init__.py" else module_name(path).rpartition(".")[0]
    refs: list[ImportRef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            refs += [ImportRef(node.lineno, alias.name, ()) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package.split(".")[: len(package.split(".")) - (node.level - 1)]
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            refs.append(ImportRef(node.lineno, module, tuple(a.name for a in node.names)))
    return refs


def calls_named(path: Path, name: str) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name
    ]


def classes_defined_in(path: Path) -> list[type]:
    module = importlib.import_module(module_name(path))
    return [obj for obj in vars(module).values() if inspect.isclass(obj) and obj.__module__ == module.__name__]


def starts_with(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")

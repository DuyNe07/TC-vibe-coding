"""Dependency rules between packages and layers (docs/rules/02-backend-architecture.md)."""

import ast

import pytest

from tests.architecture.helpers import (
    BACKEND,
    BACKEND_FEATURES,
    FRONTEND,
    FRONTEND_FEATURES,
    ROOT,
    calls_named,
    feature_keys,
    imports_of,
    python_files,
    rel,
    starts_with,
)

# layer -> feature-internal modules it may import (core + shared are always allowed)
ALLOWED_INTERNAL = {
    "models": {"models"},
    "constants": {"models"},
    "exceptions": set(),
    "dto": {"dto", "models"},
    "business": {"business", "models", "constants", "exceptions"},
    "builders": {"builders", "models", "dto", "constants", "exceptions"},
    "repositories": {"repositories", "models", "constants", "exceptions"},
    "services": {"models", "dto", "business", "builders", "repositories", "constants", "exceptions"},
    "controllers": {"services", "dto"},
}
FILE_IO_LIBS = ("openpyxl", "docx", "docxtpl", "pypdf", "xlrd")
BE_KEYS = feature_keys(BACKEND_FEATURES)
FE_KEYS = feature_keys(FRONTEND_FEATURES)


def test_backend_never_imports_streamlit_or_frontend() -> None:
    errors = [
        f"{rel(p)}:{r.lineno} imports {r.module}"
        for p in python_files(BACKEND)
        for r in imports_of(p)
        if starts_with(r.module, "streamlit") or starts_with(r.module, "frontend")
    ]
    assert not errors, "Backend must stay UI-free:\n" + "\n".join(errors)


def test_core_and_shared_do_not_depend_on_features() -> None:
    errors = []
    for folder in ("core", "shared"):
        for path in python_files(BACKEND / folder):
            for ref in imports_of(path):
                bad = ["backend.features"] + (["backend.shared"] if folder == "core" else [])
                if any(starts_with(ref.module, b) for b in bad):
                    errors.append(f"{rel(path)}:{ref.lineno} imports {ref.module}")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("key", BE_KEYS)
def test_backend_feature_imports(key: str) -> None:
    prefix = f"backend.features.{key}"
    errors = []
    for path in python_files(BACKEND_FEATURES / key):
        parts = path.relative_to(BACKEND_FEATURES / key).parts
        layer = parts[0] if len(parts) > 1 else path.stem
        if layer in ("tests", "__init__"):
            continue
        for ref in imports_of(path):
            where = f"{rel(path)}:{ref.lineno}"
            if starts_with(ref.module, "backend.features") and not starts_with(ref.module, prefix):
                errors.append(f"{where} imports another feature ({ref.module}). Features are independent.")
            elif starts_with(ref.module, prefix):
                target = ref.module[len(prefix) + 1 :].split(".")[0]
                if target and target != layer and target not in ALLOWED_INTERNAL.get(layer, set()):
                    errors.append(f"{where}: layer '{layer}' must not import '{target}' ({ref.module})")
                elif target == layer and layer in ("services", "controllers"):
                    errors.append(f"{where}: {layer} must not import other {layer}")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("key", FE_KEYS)
def test_frontend_feature_imports(key: str) -> None:
    errors = []
    for path in python_files(FRONTEND_FEATURES / key):
        for ref in imports_of(path):
            where = f"{rel(path)}:{ref.lineno}"
            module = ref.module
            if starts_with(module, "frontend.features") and not starts_with(module, f"frontend.features.{key}"):
                errors.append(f"{where} imports another frontend feature ({module})")
            elif starts_with(module, "backend.features"):
                if module != f"backend.features.{key}" and not starts_with(module, f"backend.features.{key}.dto"):
                    errors.append(
                        f"{where}: pages import only the feature root (controller) and its dto/: "
                        f"'from backend.features.{key} import XxxController' ({module})"
                    )
            elif starts_with(module, "backend") and not starts_with(module, "backend.core"):
                errors.append(f"{where}: frontend may import backend.core + its feature root/dto only ({module})")
            elif any(starts_with(module, lib) for lib in FILE_IO_LIBS):
                errors.append(f"{where}: file processing ({module}) belongs in the backend")
    assert not errors, "\n".join(errors)


def test_frontend_core_is_generic() -> None:
    errors = [
        f"{rel(p)}:{r.lineno} imports {r.module}"
        for folder in ("core", "home")
        for p in python_files(FRONTEND / folder)
        for r in imports_of(p)
        if starts_with(r.module, "frontend.features") or starts_with(r.module, "backend.features")
    ]
    assert not errors, "frontend/core and frontend/home must not depend on features:\n" + "\n".join(errors)


def test_no_print_and_no_raw_open_in_app_code() -> None:
    errors = []
    for path in [*python_files(BACKEND), *python_files(FRONTEND)]:
        if "tests" in path.relative_to(ROOT).parts:
            continue
        errors += [f"{rel(path)}:{line} uses print() - use get_logger()" for line in calls_named(path, "print")]
        if path.is_relative_to(FRONTEND):
            errors += [
                f"{rel(path)}:{line} uses open() - file I/O belongs in the backend"
                for line in calls_named(path, "open")
            ]
    assert not errors, "\n".join(errors)


def test_pages_open_controllers_through_the_gateway() -> None:
    errors = []
    for path in python_files(FRONTEND):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id.endswith("Controller"):
                errors.append(f"{rel(path)}:{node.lineno} creates {node.func.id}() - use gateway.open({node.func.id})")
    assert not errors, "\n".join(errors)

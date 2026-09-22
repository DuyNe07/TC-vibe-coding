"""Folder layout rules (docs/rules/01-project-structure.md)."""

import pytest

from backend.core.naming import is_valid_feature_key
from tests.architecture.helpers import (
    BACKEND,
    BACKEND_FEATURES,
    BUSINESS_DOCS,
    FRONTEND,
    FRONTEND_FEATURES,
    feature_keys,
    rel,
)

BACKEND_LAYERS = ("models", "dto", "business", "builders", "repositories", "services", "controllers", "tests")
BACKEND_ROOT_FILES = {"__init__.py", "constants.py", "exceptions.py"}
FRONTEND_LAYERS = ("pages", "components")
FRONTEND_ROOT_FILES = {"__init__.py", "manifest.py"}

BE_KEYS = feature_keys(BACKEND_FEATURES)
FE_KEYS = feature_keys(FRONTEND_FEATURES)


def test_all_features_and_home_load() -> None:
    from frontend.core.registry import FeatureRegistry
    from frontend.home.home_page import HomePage

    registry = FeatureRegistry.discover()
    assert not registry.errors, "\n\n".join(f"[{e.feature_key}]\n{e.traceback}" for e in registry.errors)
    for manifest in registry.features:
        for page_cls in manifest.pages:
            page_cls(manifest.key)  # pages must construct without errors
    HomePage()


def test_every_feature_exists_in_backend_and_frontend() -> None:
    assert set(BE_KEYS) == set(FE_KEYS), (
        f"Backend-only: {sorted(set(BE_KEYS) - set(FE_KEYS))}, frontend-only: {sorted(set(FE_KEYS) - set(BE_KEYS))}. "
        "Create features with scripts/new_feature.py so both sides exist."
    )


@pytest.mark.parametrize("key", BE_KEYS)
def test_feature_key_is_valid(key: str) -> None:
    assert is_valid_feature_key(key), f"Invalid feature key {key!r}: snake_case, 3-50 chars, not reserved"


@pytest.mark.parametrize("key", BE_KEYS)
def test_feature_has_business_document(key: str) -> None:
    assert (BUSINESS_DOCS / f"{key}.md").exists(), f"Missing docs/business/{key}.md (business spec is mandatory)"


@pytest.mark.parametrize("key", BE_KEYS)
def test_backend_feature_layout(key: str) -> None:
    base = BACKEND_FEATURES / key
    for layer in BACKEND_LAYERS:
        assert (base / layer / "__init__.py").exists(), f"Missing {rel(base / layer)}/__init__.py"
    root_py = {p.name for p in base.glob("*.py")}
    assert root_py >= BACKEND_ROOT_FILES, f"{rel(base)} must contain {sorted(BACKEND_ROOT_FILES)}"
    extra = root_py - BACKEND_ROOT_FILES
    assert not extra, f"{rel(base)}: move {sorted(extra)} into a layer folder ({', '.join(BACKEND_LAYERS)})"
    unknown_dirs = {p.name for p in base.iterdir() if p.is_dir() and p.name != "__pycache__"} - set(BACKEND_LAYERS)
    assert not unknown_dirs, f"{rel(base)}: unknown folders {sorted(unknown_dirs)}; allowed: {BACKEND_LAYERS}"


@pytest.mark.parametrize("key", FE_KEYS)
def test_frontend_feature_layout(key: str) -> None:
    base = FRONTEND_FEATURES / key
    for layer in FRONTEND_LAYERS:
        assert (base / layer / "__init__.py").exists(), f"Missing {rel(base / layer)}/__init__.py"
    root_py = {p.name for p in base.glob("*.py")}
    assert root_py == FRONTEND_ROOT_FILES, f"{rel(base)} root must contain exactly {sorted(FRONTEND_ROOT_FILES)}"
    unknown_dirs = {p.name for p in base.iterdir() if p.is_dir() and p.name != "__pycache__"} - set(FRONTEND_LAYERS)
    assert not unknown_dirs, f"{rel(base)}: unknown folders {sorted(unknown_dirs)}; allowed: {FRONTEND_LAYERS}"


def test_every_python_folder_is_a_package() -> None:
    missing = []
    for base in (BACKEND, FRONTEND):
        for folder in [base, *[p for p in base.rglob("*") if p.is_dir()]]:
            if "__pycache__" in folder.parts:
                continue
            if any(folder.glob("*.py")) and not (folder / "__init__.py").exists():
                missing.append(rel(folder))
    assert not missing, f"Add __init__.py to: {missing}"

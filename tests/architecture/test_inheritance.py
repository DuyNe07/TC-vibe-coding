"""OOP rules: every class inherits the base class of its layer (docs/rules/03-base-classes-and-oop.md)."""

import ast
from enum import Enum

import pytest

from backend.core.base import (
    BaseBuilder,
    BaseBusiness,
    BaseBusinessRule,
    BaseController,
    BaseDTO,
    BaseEntity,
    BaseRepository,
    BaseService,
    BaseValueObject,
)
from backend.core.exceptions import AppError
from backend.core.naming import to_snake_case
from frontend.core.base_page import BasePage
from frontend.core.feature_manifest import FeatureManifest
from tests.architecture.helpers import (
    BACKEND_FEATURES,
    BUSINESS_DOCS,
    FRONTEND_FEATURES,
    classes_defined_in,
    feature_keys,
    python_files,
    rel,
)

LAYER_BASES: dict[str, tuple[type, ...]] = {
    "models": (BaseEntity, BaseValueObject, Enum),
    "dto": (BaseDTO, Enum),
    "business": (BaseBusiness, BaseBusinessRule),
    "builders": (BaseBuilder,),
    "repositories": (BaseRepository,),
    "services": (BaseService,),
    "controllers": (BaseController,),
}
BE_KEYS = feature_keys(BACKEND_FEATURES)
FE_KEYS = feature_keys(FRONTEND_FEATURES)


def layer_files(key: str, layer: str):
    return [p for p in python_files(BACKEND_FEATURES / key / layer) if p.name != "__init__.py"]


@pytest.mark.parametrize("key", BE_KEYS)
def test_layer_classes_inherit_their_base(key: str) -> None:
    errors = []
    for layer, bases in LAYER_BASES.items():
        for path in layer_files(key, layer):
            for cls in classes_defined_in(path):
                if not issubclass(cls, bases):
                    names = " / ".join(b.__name__ for b in bases)
                    errors.append(f"{rel(path)}: {cls.__name__} must inherit {names}")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("key", BE_KEYS)
def test_feature_root_files(key: str) -> None:
    base = BACKEND_FEATURES / key
    errors = [
        f"{rel(base / 'exceptions.py')}: {c.__name__} must inherit AppError"
        for c in classes_defined_in(base / "exceptions.py")
        if not issubclass(c, AppError)
    ]
    for name in ("constants.py",):
        errors += [
            f"{rel(base / name)}: classes are not allowed here ({c.__name__})" for c in classes_defined_in(base / name)
        ]
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("key", BE_KEYS)
def test_one_service_per_file_and_thin_controllers(key: str) -> None:
    errors, services = [], []
    for path in layer_files(key, "services"):
        found = [c for c in classes_defined_in(path) if issubclass(c, BaseService)]
        if len(found) != 1:
            errors.append(f"{rel(path)}: exactly ONE service class per file (found {len(found)})")
            continue
        service = found[0]
        services.append(service)
        if not service.__name__.endswith("Service") or path.stem != to_snake_case(service.__name__):
            errors.append(f"{rel(path)}: class must be named XxxService and file xxx_service.py ({service.__name__})")
    # every service is called by exactly one controller method; controller methods only delegate
    called: list[str] = []
    for path in layer_files(key, "controllers"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                body = [n for n in node.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
                if len(body) != 1 or not isinstance(body[0], ast.Return):
                    errors.append(
                        f"{rel(path)}:{node.lineno} {node.name}(): must be one line `return XxxService().handle(request)`"
                    )
                called += [n.id for n in ast.walk(node) if isinstance(n, ast.Name) and n.id.endswith("Service")]
    for service in services:
        if called.count(service.__name__) != 1:
            errors.append(
                f"{service.__name__} must be called by exactly one controller method (found {called.count(service.__name__)})"
            )
    for path in layer_files(key, "controllers"):
        for c in classes_defined_in(path):
            if not c.__name__.endswith("Controller"):
                errors.append(f"{rel(path)}: {c.__name__} must be named XxxController")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("key", BE_KEYS)
def test_business_rule_codes_exist_in_business_doc(key: str) -> None:
    doc = (BUSINESS_DOCS / f"{key}.md").read_text(encoding="utf-8") if (BUSINESS_DOCS / f"{key}.md").exists() else ""
    missing = [
        f"{c.__name__}.code = {c.code!r}"
        for path in layer_files(key, "business")
        for c in classes_defined_in(path)
        if issubclass(c, BaseBusinessRule) and c.code and c.code not in doc
    ]
    assert not missing, f"Rule codes not found in docs/business/{key}.md: {missing}"


@pytest.mark.parametrize("key", FE_KEYS)
def test_frontend_pages_and_manifest(key: str) -> None:
    import importlib

    manifest = importlib.import_module(f"frontend.features.{key}.manifest").FEATURE
    assert isinstance(manifest, FeatureManifest), "manifest.py must define FEATURE = FeatureManifest(...)"
    assert manifest.key == key, f"FEATURE.key must be {key!r}"
    pages = []
    for path in python_files(FRONTEND_FEATURES / key / "pages"):
        if path.name == "__init__.py":
            continue
        for cls in classes_defined_in(path):
            assert issubclass(cls, BasePage), f"{rel(path)}: {cls.__name__} must inherit BasePage"
            pages.append(cls)
    orphans = [p.__name__ for p in pages if p not in manifest.pages]
    assert not orphans, f"Pages not listed in FEATURE.pages: {orphans}"


@pytest.mark.parametrize("key", BE_KEYS)
def test_one_controller_exported_by_feature_root(key: str) -> None:
    import importlib

    defined = [
        c for path in layer_files(key, "controllers") for c in classes_defined_in(path) if issubclass(c, BaseController)
    ]
    assert len(defined) == 1, (
        f"backend/features/{key}/controllers/ must define exactly ONE controller (found {len(defined)})"
    )
    root = importlib.import_module(f"backend.features.{key}")
    exported = [v for v in vars(root).values() if isinstance(v, type) and issubclass(v, BaseController)]
    assert exported == defined, (
        f"backend/features/{key}/__init__.py must export its controller: "
        f"'from backend.features.{key}.controllers.{key}_controller import {defined[0].__name__}'"
    )

"""Naming conventions shared by backend, frontend, scripts and architecture tests."""

import re

FEATURES_PACKAGE = "backend.features"
FRONTEND_FEATURES_PACKAGE = "frontend.features"

FEATURE_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,48}[a-z0-9]$")
ROUTE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
PAGE_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
RULE_CODE_PATTERN = re.compile(r"^BR-\d{2,3}$")
RESERVED_FEATURE_KEYS = frozenset({"home", "core", "shared", "api", "features", "root", "index"})


def is_valid_feature_key(key: str) -> bool:
    return bool(FEATURE_KEY_PATTERN.match(key)) and key not in RESERVED_FEATURE_KEYS


def feature_key_from_module(module_name: str, package: str = FEATURES_PACKAGE) -> str | None:
    """``backend.features.leave_request.services.x`` -> ``leave_request``."""
    prefix = package + "."
    if not module_name.startswith(prefix):
        return None
    return module_name[len(prefix) :].split(".")[0]


def feature_url_slug(feature_key: str) -> str:
    """URL segment of a feature: ``leave_request`` -> ``leave-request``."""
    return feature_key.replace("_", "-")


def to_pascal_case(snake: str) -> str:
    return "".join(part.capitalize() for part in snake.split("_") if part)


def to_snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

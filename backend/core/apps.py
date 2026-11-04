"""Registered apps (``backend/app_registry.py``): URL prefix per app, used by the router and the gateway."""

import re
from functools import cache

from backend.core.exceptions import ConfigurationError
from backend.core.naming import feature_url_slug, is_valid_feature_key

PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9]{1,29}$")  # no "-": it separates the prefix from the app in URLs
REGISTRY_FILE = "backend/app_registry.py"


@cache
def registered_apps() -> dict[str, str]:
    """``{feature_key: url prefix}`` from the registry, validated once per process."""
    from backend.app_registry import APPS

    apps: dict[str, str] = {}
    for prefix, key in APPS:
        if not PREFIX_PATTERN.match(prefix):
            raise ConfigurationError(f"{REGISTRY_FILE}: prefix {prefix!r} must be lower-case letters and digits")
        if not is_valid_feature_key(key):
            raise ConfigurationError(f"{REGISTRY_FILE}: {key!r} is not a valid feature key")
        if key in apps:
            raise ConfigurationError(f"{REGISTRY_FILE}: app {key!r} is registered twice")
        apps[key] = prefix
    return apps


def is_registered(feature_key: str) -> bool:
    return feature_key in registered_apps()


def ensure_registered(feature_key: str) -> None:
    if not is_registered(feature_key):
        raise ConfigurationError(
            f'App {feature_key!r} is not registered: add ("<prefix>", "{feature_key}") to APPS in {REGISTRY_FILE}'
        )


def app_url_path(feature_key: str) -> str:
    """URL of an app's landing page without the leading "/": ``anhthy`` + ``leave_request`` -> ``anhthy-leave-request``.
    (Streamlit 1.64 refuses nested URL paths, so the prefix is joined with "-", not "/".)"""
    ensure_registered(feature_key)
    return f"{registered_apps()[feature_key]}-{feature_url_slug(feature_key)}"

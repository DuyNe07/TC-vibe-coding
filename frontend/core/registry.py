"""Auto-discovers frontend features: every ``frontend/features/<key>/manifest.py`` exposing ``FEATURE``.

A feature that fails to import is reported (Home page shows the error) without breaking the others.
"""

import importlib
import pkgutil
import traceback
from dataclasses import dataclass, field

from backend.core.logger import get_logger
from frontend.core.feature_manifest import FeatureManifest

FRONTEND_FEATURES_PACKAGE = "frontend.features"
logger = get_logger(__name__)


@dataclass(frozen=True)
class FeatureLoadError:
    feature_key: str
    message: str
    traceback: str


@dataclass
class FeatureRegistry:
    features: list[FeatureManifest] = field(default_factory=list)
    errors: list[FeatureLoadError] = field(default_factory=list)

    @classmethod
    def discover(cls, package: str = FRONTEND_FEATURES_PACKAGE) -> "FeatureRegistry":
        registry = cls()
        root = importlib.import_module(package)
        for info in pkgutil.iter_modules(root.__path__):
            if not info.ispkg or info.name.startswith("_"):
                continue
            try:
                manifest = importlib.import_module(f"{package}.{info.name}.manifest").FEATURE
                if not isinstance(manifest, FeatureManifest):
                    raise TypeError("FEATURE must be a FeatureManifest instance")
                if manifest.key != info.name:
                    raise ValueError(f"FEATURE.key {manifest.key!r} must equal folder name {info.name!r}")
                if manifest.enabled:
                    registry.features.append(manifest)
            except Exception as exc:
                logger.exception("Cannot load frontend feature %s", info.name)
                registry.errors.append(FeatureLoadError(info.name, str(exc), traceback.format_exc()))
        registry.features.sort(key=lambda m: (m.order, m.title))
        return registry

    def get(self, key: str) -> FeatureManifest | None:
        return next((m for m in self.features if m.key == key), None)

    def groups(self) -> dict[str, list[FeatureManifest]]:
        grouped: dict[str, list[FeatureManifest]] = {}
        for manifest in self.features:
            grouped.setdefault(manifest.group, []).append(manifest)
        return grouped

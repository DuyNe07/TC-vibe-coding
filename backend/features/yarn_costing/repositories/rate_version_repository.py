"""Stored in data/yarn_costing/rate_versions.json (starts empty: versions come from UC-04 / UC-34)."""

import json

from backend.features.yarn_costing.models.rate_version import RateVersion
from backend.features.yarn_costing.repositories.legacy_conversion import convert_rate_version
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class RateVersionRepository(SafeJsonRepository[RateVersion]):
    storage_file = "rate_versions.json"

    def _read(self) -> dict[str, RateVersion]:
        if not self.file_path.exists():
            return {}
        raw = json.loads(self.file_path.read_text(encoding="utf-8") or "[]")
        versions = [RateVersion.model_validate(convert_rate_version(item)) for item in raw]
        return {v.id: v for v in versions}

    def for_factory(self, factory_code: str) -> list[RateVersion]:
        """Newest first."""
        return sorted(
            self.find(lambda v: v.factory_code.value == factory_code), key=lambda v: v.created_at, reverse=True
        )

    def current(self, factory_code: str) -> RateVersion | None:
        """4.5: the newest version is the one in use."""
        versions = self.for_factory(factory_code)
        return versions[0] if versions else None

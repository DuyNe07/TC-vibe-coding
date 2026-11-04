"""Table xuan2894__yarn_costing__rate_version (starts empty: versions come from UC-04 / UC-34)."""

from typing import Any

from backend.features.yarn_costing.models.rate_version import RateVersion
from backend.features.yarn_costing.repositories.legacy_conversion import convert_rate_version
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class RateVersionRepository(YarnSqlRepository[RateVersion]):
    legacy_file = "rate_versions.json"

    def _convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [convert_rate_version(item) for item in raw]

    def for_factory(self, factory_code: str) -> list[RateVersion]:
        """Newest first."""
        return sorted(
            self.find(lambda v: v.factory_code.value == factory_code), key=lambda v: v.created_at, reverse=True
        )

    def current(self, factory_code: str) -> RateVersion | None:
        """4.5: the newest version is the one in use."""
        versions = self.for_factory(factory_code)
        return versions[0] if versions else None

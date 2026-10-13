"""Table xuan2894__yarn_costing__yarn: yarns with their price lines and stage cost details.

Yarns stored by the previous version (blend_ratios + carding NSM) are converted to components when imported (BR-58)."""

from typing import Any

from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.legacy_conversion import convert_yarn, needs_yarn_conversion
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class YarnRepository(YarnSqlRepository[Yarn]):
    legacy_file = "yarns.json"

    def _convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not any(needs_yarn_conversion(item) for item in raw):
            return raw
        groups: dict[str, dict] = {}
        for group in LossGroupRepository().list_all():
            groups.setdefault(group.factory_code.value, {})[group.group_key] = group
        return [
            convert_yarn(item, groups.get(item.get("factory_code", ""), {})) if needs_yarn_conversion(item) else item
            for item in raw
        ]

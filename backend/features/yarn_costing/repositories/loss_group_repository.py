"""Table xuan2894__yarn_costing__loss_group (starts empty). Old S4 losses C3.1..C3.3 are imported as C3 (BR-59)."""

from typing import Any

from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.repositories.legacy_conversion import convert_loss_group
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class LossGroupRepository(YarnSqlRepository[LossGroup]):
    legacy_file = "loss_groups.json"

    def _convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [convert_loss_group(item) for item in raw]

    def for_factory(self, factory_code: str) -> list[LossGroup]:
        return sorted(self.find(lambda g: g.factory_code.value == factory_code), key=lambda g: g.group_key)

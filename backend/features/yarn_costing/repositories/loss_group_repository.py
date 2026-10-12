"""Stored in data/yarn_costing/loss_groups.json (starts empty). Old S4 losses C3.1..C3.3 are read as C3 (BR-59)."""

import json

from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.repositories.legacy_conversion import convert_loss_group
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


class LossGroupRepository(SafeJsonRepository[LossGroup]):
    storage_file = "loss_groups.json"

    def _read(self) -> dict[str, LossGroup]:
        if not self.file_path.exists():
            return {}
        raw = json.loads(self.file_path.read_text(encoding="utf-8") or "[]")
        groups = [LossGroup.model_validate(convert_loss_group(item)) for item in raw]
        return {g.id: g for g in groups}

    def for_factory(self, factory_code: str) -> list[LossGroup]:
        return sorted(self.find(lambda g: g.factory_code.value == factory_code), key=lambda g: g.group_key)

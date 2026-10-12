"""Stored in data/yarn_costing/yarns.json: yarns with their price lines and stage cost details (compact JSON).

Yarns stored by the previous version (blend_ratios + carding NSM) are converted to components when read (BR-58)."""

import json

from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.compact_json_repository import CompactJsonRepository
from backend.features.yarn_costing.repositories.legacy_conversion import convert_yarn, needs_yarn_conversion
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository


class YarnRepository(CompactJsonRepository[Yarn]):
    storage_file = "yarns.json"

    def _read(self) -> dict[str, Yarn]:
        if not self.file_path.exists():
            return {}
        raw = json.loads(self.file_path.read_text(encoding="utf-8") or "[]")
        if any(needs_yarn_conversion(item) for item in raw):
            groups_repo = LossGroupRepository(self.file_path.parent / LossGroupRepository.storage_file)
            groups = {}
            for group in groups_repo.list_all():
                groups.setdefault(group.factory_code.value, {})[group.group_key] = group
            raw = [
                convert_yarn(item, groups.get(item.get("factory_code", ""), {}))
                if needs_yarn_conversion(item)
                else item
                for item in raw
            ]
        yarns = [Yarn.model_validate(item) for item in raw]
        return {y.id: y for y in yarns}

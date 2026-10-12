"""Stored in data/yarn_costing/stages.json. Seeds tables 4.4.1 (S4) and 4.4.2 (S1) on first read.

Rows stored by the previous version (C3.1 / C3.2 / C3.3, old blend slots) are converted when read."""

import json

from backend.features.yarn_costing.constants import PACKAGING_STAGE_CODE, SEED_STAGES
from backend.features.yarn_costing.models.enums import FactoryCode, RateCodeSource, RecoveryType, SecondaryMethod
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.repositories.legacy_conversion import convert_stages, needs_stage_conversion
from backend.features.yarn_costing.repositories.safe_json_repository import SafeJsonRepository


def _seed() -> list[Stage]:
    stages = []
    for factory, rows in SEED_STAGES.items():
        for seq, code, name, group, recovery, slot, merge, method, cumulative, varies, passes in rows:
            packaging = code == PACKAGING_STAGE_CODE
            stages.append(
                Stage(
                    factory_code=FactoryCode(factory),
                    stage_code=code,
                    stage_name=name,
                    stage_group=group,
                    sequence=seq,
                    is_packaging=packaging,
                    recovery_type=RecoveryType(recovery),
                    blend_slot=slot,
                    is_carding=passes is not None,
                    max_passes=passes,
                    is_merge_stage=merge,
                    secondary_method=SecondaryMethod(method),
                    cumulative_stages=list(cumulative),
                    varies_with_count=varies,
                    rate_code_source=RateCodeSource.LOAI_DONG_GOI if packaging else RateCodeSource.CHINH_CONG_DOAN,
                )
            )
    return stages


class StageRepository(SafeJsonRepository[Stage]):
    storage_file = "stages.json"

    def _read(self) -> dict[str, Stage]:
        if not self.file_path.exists():
            with self._lock:
                if not self.file_path.exists():
                    self._save({s.id: s for s in _seed()})
        raw = json.loads(self.file_path.read_text(encoding="utf-8") or "[]")
        if needs_stage_conversion(raw):
            raw = convert_stages(raw)
        stages = [Stage.model_validate(item) for item in raw]
        return {s.id: s for s in stages}

    def for_factory(self, factory_code: str) -> list[Stage]:
        return sorted(self.find(lambda s: s.factory_code.value == factory_code), key=lambda s: s.sequence)

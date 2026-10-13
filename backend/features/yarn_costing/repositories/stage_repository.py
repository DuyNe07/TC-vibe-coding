"""Table yarn_costing__stage. Seeds tables 4.4.1 (S4) and 4.4.2 (S1) on first read.

Rows stored by the previous version (C3.1 / C3.2 / C3.3, old blend slots) are converted when imported."""

from typing import Any

from backend.features.yarn_costing.constants import PACKAGING_STAGE_CODE, SEED_STAGES
from backend.features.yarn_costing.models.enums import FactoryCode, RateCodeSource, RecoveryType, SecondaryMethod
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.repositories.legacy_conversion import convert_stages, needs_stage_conversion
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


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


class StageRepository(YarnSqlRepository[Stage]):
    legacy_file = "stages.json"

    def _seed(self) -> list[Stage]:
        return _seed()

    def _convert(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return convert_stages(raw) if needs_stage_conversion(raw) else raw

    def for_factory(self, factory_code: str) -> list[Stage]:
        return sorted(self.find(lambda s: s.factory_code.value == factory_code), key=lambda s: s.sequence)

"""4.4 Công đoạn và cấu hình tính (Stage)."""

from pydantic import Field

from backend.core.base import BaseEntity
from backend.features.yarn_costing.models.enums import FactoryCode, RateCodeSource, RecoveryType, SecondaryMethod

NO_BLEND_SLOT = "Không"
PASS_RATIO_SLOT = "Tỷ lệ của lượt"
LINE_RATIO_PREFIX = "Tỷ lệ dây chuyền "


class Stage(BaseEntity):
    factory_code: FactoryCode
    stage_code: str = Field(min_length=1, max_length=20)
    stage_name: str = Field(min_length=1, max_length=100)
    stage_group: str = Field(min_length=1, max_length=20)
    sequence: int = Field(ge=1)
    is_packaging: bool = False
    recovery_type: RecoveryType = RecoveryType.KHONG
    blend_slot: str = NO_BLEND_SLOT
    is_carding: bool = False
    max_passes: int | None = Field(default=None, ge=1, le=3)
    is_merge_stage: bool = False
    secondary_method: SecondaryMethod = SecondaryMethod.BINH_QUAN
    cumulative_stages: list[str] = Field(default_factory=list)
    varies_with_count: bool = False
    rate_code_source: RateCodeSource = RateCodeSource.CHINH_CONG_DOAN

    @property
    def uses_pass_ratio(self) -> bool:
        """blend_slot 'Tỷ lệ của lượt' (BR-17)."""
        return self.blend_slot == PASS_RATIO_SLOT

    @property
    def ratio_line(self) -> str | None:
        """blend_slot 'Tỷ lệ dây chuyền X' → X (BR-17)."""
        if self.blend_slot.startswith(LINE_RATIO_PREFIX):
            return self.blend_slot[len(LINE_RATIO_PREFIX) :].strip()
        return None

    @property
    def pass_limit(self) -> int:
        """BR-56: maximum number of materials on a carding line (1 when not set)."""
        return self.max_passes or 1

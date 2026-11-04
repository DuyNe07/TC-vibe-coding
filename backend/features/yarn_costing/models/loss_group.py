"""4.11 Nhóm tiêu hao (Loss group)."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.yarn_costing.models.enums import FactoryCode, LossGroupLevel, Technology


class LossComponent(BaseValueObject):
    component_group_key: str = Field(min_length=1, max_length=200)
    ratio: Decimal = Field(gt=0, le=1)
    slot: str = ""  # S4 file only: component column of sheet '2. Input tieu hao' (PE, Other - C3.1, ..., Cotton)


class LossGroup(BaseEntity):
    factory_code: FactoryCode
    group_key: str = Field(min_length=1, max_length=200)
    yarn_group_label: str = Field(min_length=1, max_length=200)
    material: str = Field(default="", max_length=200)
    technology: Technology
    level: LossGroupLevel = LossGroupLevel.SO_CAP
    losses: dict[str, Decimal] = Field(default_factory=dict)
    components: list[LossComponent] = Field(default_factory=list)
    updated_by: str = ""

    @property
    def material_tech_key(self) -> str:
        return f"{self.material} - {self.technology.value}"

    @property
    def material_label(self) -> str:
        """Name used as material_label of a yarn component (4.12.1): material_tech_key, or the group name when the
        group has no material."""
        return self.material_tech_key if self.material.strip() else self.yarn_group_label

    def loss_at(self, stage_code: str) -> Decimal:
        return self.losses.get(stage_code, Decimal(0))

    def carding_lines_with_loss(self, carding_codes: list[str]) -> list[str]:
        """Carding lines (in the given order) where this group declares a loss > 0."""
        return [code for code in carding_codes if self.loss_at(code) > 0]

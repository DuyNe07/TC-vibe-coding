"""Value objects used by the price calculation (BR-13..BR-23) and the recalculation (BR-36)."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.models.rate_version import RateLine, RateVersion
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import CostBreakdown, StageCostDetail, Yarn, YarnComponent


class FactoryData(BaseValueObject):
    """Everything the calculation needs for one factory (loaded once per use case)."""

    factory_code: FactoryCode
    stages: list[Stage] = Field(default_factory=list)
    recovery: dict[str, Decimal] = Field(default_factory=dict)
    rate_version: RateVersion | None = None
    rates: dict[str, RateLine] = Field(default_factory=dict)
    packaging: dict[str, PackagingType] = Field(default_factory=dict)
    loss_groups: dict[str, LossGroup] = Field(default_factory=dict)
    routes: list[ProcessRoute] = Field(default_factory=list)
    trial_factor: Decimal = Decimal(3)

    def stage(self, stage_code: str) -> Stage | None:
        return next((s for s in self.stages if s.stage_code == stage_code), None)

    @property
    def stage_codes(self) -> list[str]:
        return [s.stage_code for s in self.stages]

    @property
    def nsm_stage_codes(self) -> list[str]:
        return [s.stage_code for s in self.stages if not s.is_packaging]

    @property
    def carding_stages(self) -> list[Stage]:
        """4.3 / 4.4: carding lines (is_carding) in sequence order."""
        return sorted((s for s in self.stages if s.is_carding), key=lambda s: s.sequence)

    @property
    def carding_codes(self) -> list[str]:
        return [s.stage_code for s in self.carding_stages]


class CostResult(BaseValueObject):
    passed: bool
    reasons: list[str] = Field(default_factory=list)
    details: list[StageCostDetail] = Field(default_factory=list)
    cost: CostBreakdown = Field(default_factory=CostBreakdown)


class ParsedYarnName(BaseValueObject):
    valid: bool
    yarn_group: str = ""
    count: Decimal | None = None
    count_text: str = ""
    loss_group_key: str = ""
    technology_is_mvs: bool = False
    is_compact: bool = False


class RecalcOutcome(BaseValueObject):
    yarns: list[Yarn] = Field(default_factory=list)
    history: list[PriceHistory] = Field(default_factory=list)
    yarn_count: int = 0
    failed_yarn_count: int = 0
    changed_line_count: int = 0
    line_count: int = 0


class NsmInput(BaseValueObject):
    """Target of the NSM validation rules (BR-09..BR-12, BR-32, BR-33, BR-38)."""

    yarn_code: str
    components: list[YarnComponent] = Field(default_factory=list)
    nsm: dict[str, Decimal] = Field(default_factory=dict)
    max_passes: dict[str, int] = Field(default_factory=dict)  # carding line → BR-56 limit
    group_key: str = ""
    material_options: list[str] = Field(default_factory=list)  # BR-57 (empty = free text)
    is_compact: bool = False
    has_compact_stage: bool = False
    packaging_valid: bool = True
    is_locked: bool = False
    adjust_reason: str = ""
    warning_stages: list[str] = Field(default_factory=list)
    reference_yarn_code: str = ""
    warning_reason: str = ""


class AdjustmentInput(BaseValueObject):
    """Target of BR-34 (dòng chiết khấu / phụ phí)."""

    percent: Decimal
    reason: str = ""
    order_ref: str = ""


class PricingPreview(BaseValueObject):
    """UC-21 / UC-23 / UC-24: yarn with the entered NSM, its calculation and the NSM warning (BR-38)."""

    candidate: Yarn
    result: CostResult
    reference_yarn_code: str | None = None
    warning_stages: list[str] = Field(default_factory=list)

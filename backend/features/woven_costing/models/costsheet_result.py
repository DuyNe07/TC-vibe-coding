"""4.20 calculation results stored with each version (read-only once the version leaves Nháp / Trả lại)."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.enums import YarnDirection

ZERO = Decimal(0)


class CostWarning(BaseValueObject):
    """BR-80 one warning; ``blocking`` = must be fixed before sending for approval."""

    code: str
    message: str
    blocking: bool = False


class YarnLineResult(BaseValueObject):
    direction: YarnDirection
    seq: int
    loss_rate: Decimal = ZERO
    yarn_kg: Decimal = ZERO
    amount: Decimal = ZERO
    twist_estimate_kg: Decimal = ZERO


class TwistLineResult(BaseValueObject):
    direction: str
    count: str = ""
    quantity_kg: Decimal = ZERO
    norm: CostItems = Field(default_factory=CostItems)
    amount: Decimal = ZERO
    error: str = ""


class StageCost(BaseValueObject):
    """One line of the weaving stage table (BR-22): quantity, unit, norm per unit, factor and amount."""

    stage: str
    quantity: Decimal = ZERO
    unit: str = ""
    norm: Decimal = ZERO
    factor_applied: Decimal = Decimal(1)
    amount: Decimal = ZERO


class CostItemRow(BaseValueObject):
    """Cost per meter by item (Se, Dệt, Nhuộm)."""

    stage: str
    items: CostItems = Field(default_factory=CostItems)


class DyeingLine(BaseValueObject):
    """One dyeing line (HCM: per kg then per m; TCDN: per m)."""

    group: str
    name: str
    items: CostItems = Field(default_factory=CostItems)
    factor: Decimal = Decimal(1)
    loss_rate: Decimal = ZERO
    per_kg: Decimal = ZERO
    per_m: Decimal = ZERO
    note: str = ""


class AppliedParameter(BaseValueObject):
    """BR-46 (2026-11-25): a value taken from the tables of the parameter set for this costsheet (discount factor of
    a department, % B/C of the sale form): value of the table, value used and why (row of the table)."""

    code: str
    default_value: Decimal = ZERO
    used_value: Decimal = ZERO
    reason: str = ""
    applies: bool = True


class CostsheetResult(BaseValueObject):
    calculated: bool = False
    exchange_rate: Decimal = ZERO
    greige_meters: Decimal = ZERO
    finished_meters_needed: Decimal = ZERO
    greige_kg: Decimal = ZERO
    finished_kg: Decimal = ZERO
    greige_m_per_kg: Decimal = ZERO
    finished_m_per_kg: Decimal = ZERO
    quantity_factor: Decimal = ZERO
    shrinkage: Decimal = ZERO
    low_shrinkage: bool = False
    dye_loss_rate: Decimal = ZERO
    greige_bc_rate: Decimal = ZERO
    finished_bc_rate: Decimal = ZERO
    yarn_ratio_total: Decimal = ZERO
    yarn_total: Decimal = ZERO
    twist_estimated_kg: Decimal = ZERO
    twist_entered_kg: Decimal = ZERO
    warp_ends_total: Decimal = ZERO
    size_band: str = ""
    warping_meters: Decimal = ZERO
    weft_density_group: int = 0
    weaving_total: Decimal = ZERO
    weaving_cm_price: Decimal = ZERO
    tcdn_factor: Decimal = ZERO
    dyeing_per_kg: Decimal = ZERO
    dyeing_per_m: Decimal = ZERO
    dyeing_total: Decimal = ZERO
    bc_liquidation: Decimal = ZERO
    total_cost: Decimal = ZERO
    unit_cost_vnd: Decimal = ZERO
    cogs_extra_total: Decimal = ZERO
    cogs_vnd: Decimal = ZERO
    sell_price_vnd: Decimal = ZERO
    gp: Decimal = ZERO
    gp_pct: Decimal = ZERO
    sa: Decimal = ZERO
    commission: Decimal = ZERO
    freight_insurance: Decimal = ZERO
    interest_cost: Decimal = ZERO
    op: Decimal = ZERO
    op_pct: Decimal = ZERO
    price_with_vat: Decimal = ZERO
    gp_threshold: Decimal = ZERO
    op_threshold: Decimal = ZERO
    gp_below: bool = False
    op_below: bool = False
    yarn_lines: list[YarnLineResult] = Field(default_factory=list)
    twist_lines: list[TwistLineResult] = Field(default_factory=list)
    weaving_stages: list[StageCost] = Field(default_factory=list)
    cost_items: list[CostItemRow] = Field(default_factory=list)
    dyeing_lines: list[DyeingLine] = Field(default_factory=list)
    warnings: list[CostWarning] = Field(default_factory=list)
    applied_parameters: list[AppliedParameter] = Field(default_factory=list)

    @property
    def below_threshold(self) -> bool:
        return self.gp_below or self.op_below

    @property
    def blocking_messages(self) -> list[str]:
        return [w.message for w in self.warnings if w.blocking]


class WeavingOutcome(BaseValueObject):
    """Intermediate result of BR-20..BR-24 (copied into CostsheetResult)."""

    twist_lines: list[TwistLineResult] = Field(default_factory=list)
    stages: list[StageCost] = Field(default_factory=list)
    total: Decimal = ZERO
    twist_items_per_m: CostItems = Field(default_factory=CostItems)
    weaving_items_per_m: CostItems = Field(default_factory=CostItems)
    warp_ends_total: Decimal = ZERO
    size_band: str = ""
    warping_meters: Decimal = ZERO
    weft_density_group: int = 0
    warnings: list[CostWarning] = Field(default_factory=list)


class DyeingOutcome(BaseValueObject):
    """Intermediate result of BR-25 / BR-26 (copied into CostsheetResult)."""

    lines: list[DyeingLine] = Field(default_factory=list)
    per_kg: Decimal = ZERO
    per_m: Decimal = ZERO
    items_per_m: CostItems = Field(default_factory=CostItems)
    factor: Decimal = ZERO
    warnings: list[CostWarning] = Field(default_factory=list)

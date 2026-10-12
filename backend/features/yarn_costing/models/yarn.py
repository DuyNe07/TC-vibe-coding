"""4.12 Mã sợi / bản NSM (Yarn) with its 4.13 price lines and 4.14 stage cost details (stored together)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject, utc_now
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    LineType,
    NsmMode,
    Technology,
    YarnOrigin,
    YarnStatus,
)

ZERO = Decimal(0)


class CostBreakdown(BaseValueObject):
    """5 cost components (VND/kg)."""

    labor: Decimal = ZERO
    depreciation: Decimal = ZERO
    electricity: Decimal = ZERO
    materials: Decimal = ZERO
    overhead: Decimal = ZERO

    @property
    def total(self) -> Decimal:
        return self.labor + self.depreciation + self.electricity + self.materials + self.overhead

    def scaled(self, factor: Decimal) -> "CostBreakdown":
        return CostBreakdown(
            labor=self.labor * factor,
            depreciation=self.depreciation * factor,
            electricity=self.electricity * factor,
            materials=self.materials * factor,
            overhead=self.overhead * factor,
        )


class YarnComponent(BaseValueObject):
    """4.12.1 Thành phần nguyên liệu của sợi (material, ratio, carding line, pass, carding NSM)."""

    material_label: str = Field(min_length=1, max_length=200)
    ratio: Decimal = ZERO  # 0 ≤ x ≤ 1 checked by BR-09
    carding_stage: str = ""  # "" = Không chải thô
    pass_no: int | None = None
    nsm_carding: Decimal | None = None  # ≥ 0 checked by BR-10

    @property
    def nsm_value(self) -> Decimal:
        return self.nsm_carding or ZERO


class StageCostDetail(BaseValueObject):
    sequence: int
    stage_code: str
    stage_name: str
    material_label: str = ""
    pass_no: int | None = None
    nsm: Decimal | None = None
    run_minutes: Decimal
    loss: Decimal = ZERO
    loss_source_stage: str = ""  # BR-64: carding line the loss was taken from ("" = the running line)
    cumulative_loss: Decimal = ZERO
    total_rate: Decimal = ZERO
    cost: CostBreakdown = Field(default_factory=CostBreakdown)

    @property
    def cost_per_kg(self) -> Decimal:
        return self.cost.total

    @property
    def loss_note(self) -> str:
        """4.14 / BR-64: "Tiêu hao lấy từ <Y> (<X> chưa khai báo)" when the loss comes from the equivalent line."""
        if not self.loss_source_stage:
            return ""
        return f"Tiêu hao lấy từ {self.loss_source_stage} ({self.stage_code} chưa khai báo)"


class PriceLine(BaseValueObject):
    line_code: str = Field(min_length=1, max_length=80)
    line_type: LineType
    adjustment_percent: Decimal | None = None
    adjustment_reason: str = ""
    order_ref: str = ""
    cost: CostBreakdown = Field(default_factory=CostBreakdown)
    accounting_code: str | None = None
    accounting_code_by: str = ""
    accounting_code_at: datetime | None = None
    created_by: str = ""
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def total_vnd(self) -> Decimal:
        return self.cost.total

    @property
    def has_accounting_code(self) -> bool:
        return bool(self.accounting_code)


class Yarn(BaseEntity):
    factory_code: FactoryCode
    yarn_code: str = Field(min_length=1, max_length=60)
    base_code: str = Field(min_length=1, max_length=60)
    revision_no: int = Field(default=0, ge=0)
    yarn_name: str = Field(min_length=1, max_length=200)
    yarn_group: str = ""
    count: Decimal | None = None
    loss_group_key: str = ""
    technology: Technology = Technology.RING
    is_compact: bool = False
    packaging_code: str | None = None
    components: list[YarnComponent] = Field(default_factory=list)
    nsm: dict[str, Decimal] = Field(default_factory=dict)
    nsm_mode: NsmMode | None = None
    reference_yarn_code: str | None = None
    nsm_warning_reason: str = ""
    adjust_reason: str = ""
    status: YarnStatus = YarnStatus.CHO_XUONG_XEM
    status_reasons: list[str] = Field(default_factory=list)
    reject_reason: str = ""
    origin: YarnOrigin = YarnOrigin.YEU_CAU_SALES
    requested_by: str = ""
    requested_at: datetime = Field(default_factory=utc_now)
    handled_by: str = ""
    handled_at: datetime | None = None
    first_priced_at: date | None = None
    last_calculated_at: datetime | None = None
    effective_date: date | None = None
    lines: list[PriceLine] = Field(default_factory=list)
    stage_details: list[StageCostDetail] = Field(default_factory=list)
    max_ck_no: int = 0
    max_pp_no: int = 0
    pending_accounting_code: str | None = None

    @property
    def is_locked(self) -> bool:
        return bool(self.pending_accounting_code) or any(line.has_accounting_code for line in self.lines)

    @property
    def regular_line(self) -> PriceLine | None:
        return next((line for line in self.lines if line.line_type == LineType.THUONG), None)

    @property
    def is_base(self) -> bool:
        return self.revision_no == 0

    def nsm_at(self, stage_code: str) -> Decimal:
        return self.nsm.get(stage_code, ZERO)

    def passes_on(self, stage_code: str) -> list[YarnComponent]:
        """Components running on a carding line, in pass order (4.12.1)."""
        return [c for c in self.components if c.carding_stage == stage_code]

    def line_ratio(self, stage_code: str) -> Decimal:
        """4.12.1 line_ratio: total ratio of the components on a carding line."""
        return sum((c.ratio for c in self.passes_on(stage_code)), ZERO)

    def line(self, line_code: str) -> PriceLine | None:
        return next((line for line in self.lines if line.line_code == line_code), None)

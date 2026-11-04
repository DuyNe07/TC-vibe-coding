"""Rows read from the uploaded workbook (section 5.2) and the import plan (BR-42..BR-45)."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.process_route import ProcessRoute
from backend.features.yarn_costing.models.rate_version import RateLine
from backend.features.yarn_costing.models.yarn import CostBreakdown, Yarn


class RejectedRow(BaseValueObject):
    sheet: str
    excel_row: int
    key: str
    reason: str


class RateRow(BaseValueObject):
    excel_row: int
    stage_value: str
    group_value: str = ""
    labor: Decimal | None = None
    depreciation: Decimal | None = None
    electricity: Decimal | None = None
    materials: Decimal | None = None
    overhead: Decimal | None = None
    note: str = ""


class RecoveryRow(BaseValueObject):
    excel_row: int
    label: str
    rate: Decimal | None = None


class PackagingRow(BaseValueObject):
    excel_row: int
    code: str
    name: str = ""
    weight_kg: Decimal | None = None
    man_days: Decimal | None = None
    minutes_per_kg: Decimal | None = None


class RouteRow(BaseValueObject):
    excel_row: int
    yarn_group: str
    technology_text: str = ""
    component_count: Decimal | None = None
    route_text: str = ""


class LossRow(BaseValueObject):
    excel_row: int
    yarn_group_label: str
    material: str = ""
    technology_text: str = ""
    losses: dict[str, Decimal | None] = Field(default_factory=dict)
    component_names: list[str] = Field(default_factory=list)
    component_ratios: list[Decimal | None] = Field(default_factory=list)
    has_formula: bool = False
    bad_values: list[str] = Field(default_factory=list)


class NsmRow(BaseValueObject):
    excel_row: int
    raw_code: str = ""
    yarn_name: str
    blend_ratios: dict[str, Decimal] = Field(default_factory=dict)
    nsm: dict[str, Decimal] = Field(default_factory=dict)
    packaging_code: str = ""
    remark: str = ""
    bad_values: list[str] = Field(default_factory=list)


class PriceRow(BaseValueObject):
    excel_row: int
    raw_code: str
    cost: CostBreakdown = Field(default_factory=CostBreakdown)
    total: Decimal | None = None
    priced_date: date | None = None
    priced_date_text: str = ""
    accounting_code: str = ""


class SheetRead(BaseValueObject):
    """One sheet found in the file: its canonical name, data row count and missing required columns."""

    sheet: str
    read: int = 0
    missing_columns: list[str] = Field(default_factory=list)


class ParsedWorkbook(BaseValueObject):
    file_name: str
    sheets: list[SheetRead] = Field(default_factory=list)
    rate_rows: list[RateRow] = Field(default_factory=list)
    recovery_rows: list[RecoveryRow] = Field(default_factory=list)
    packaging_rows: list[PackagingRow] = Field(default_factory=list)
    route_rows: list[RouteRow] = Field(default_factory=list)
    loss_rows: list[LossRow] = Field(default_factory=list)
    nsm_rows: list[NsmRow] = Field(default_factory=list)
    price_rows: list[PriceRow] = Field(default_factory=list)

    def has_sheet(self, sheet: str) -> bool:
        return any(s.sheet == sheet for s in self.sheets)


class SheetPlan(BaseValueObject):
    sheet: str
    read: int = 0
    created: int = 0
    updated: int = 0
    rejected: int = 0
    skipped_message: str = ""


class ImportPlan(BaseValueObject):
    """What a commit would store (decided by business/import_business.py)."""

    sheets: list[SheetPlan] = Field(default_factory=list)
    rejected_rows: list[RejectedRow] = Field(default_factory=list)
    rate_lines: list[RateLine] | None = None
    recovery_rates: dict[str, Decimal] = Field(default_factory=dict)
    packaging: list[PackagingType] = Field(default_factory=list)
    routes: list[ProcessRoute] = Field(default_factory=list)
    loss_groups: list[LossGroup] = Field(default_factory=list)
    yarns: list[Yarn] = Field(default_factory=list)
    legacy_prices: list[PriceRow] = Field(default_factory=list)
    legacy_codes: list[str] = Field(default_factory=list)

    @property
    def valid_count(self) -> int:
        return sum(s.created + s.updated for s in self.sheets)


class HeaderMap(BaseValueObject):
    """Header of one sheet: normalized column names → sorted column indexes, and the last header row (1-based)."""

    columns: dict[str, list[int]] = Field(default_factory=dict)
    last_row: int = 0

    def col(self, key: str, occurrence: int = 0) -> int | None:
        cols = self.columns.get(key, [])
        return cols[occurrence] if len(cols) > occurrence else None

    @property
    def max_col(self) -> int:
        return max((c for cols in self.columns.values() for c in cols), default=0) + 1


# ---- 5.7 / UC-45 Khai báo thành phần sợi pha ----
class ComponentDeclRow(BaseValueObject):
    """One row of sheet 'Khai bao thanh phan' (5.7); ratios are percents as typed (48 = 48%)."""

    excel_row: int
    group_label: str
    technology_text: str = ""
    names: list[str] = Field(default_factory=list)  # Thành phần 1..5 ("" = empty)
    ratios: list[Decimal | None] = Field(default_factory=list)  # Tỷ lệ 1..5 (None = empty)
    bad_ratios: list[int] = Field(default_factory=list)  # 1-based k of ratio cells that are not numbers


class ComponentGroupChange(BaseValueObject):
    """A loss group declared by the file (BR-67): before / after."""

    excel_row: int
    group: LossGroup
    created: bool = False
    old_level: str = ""
    old_losses: dict[str, Decimal] = Field(default_factory=dict)
    affected_count: int = 0


class UnmatchedYarn(BaseValueObject):
    """BR-68: a component of a yarn that could not be matched with the new components of its loss group."""

    yarn_code: str
    yarn_name: str = ""
    material_label: str
    carding_stage: str
    group_key: str


class ComponentPlan(BaseValueObject):
    """UC-45 result of checking the file (nothing saved yet)."""

    changes: list[ComponentGroupChange] = Field(default_factory=list)
    recomputed: list[LossGroup] = Field(default_factory=list)  # secondary groups using a declared group
    rejected_rows: list[RejectedRow] = Field(default_factory=list)
    relabeled_yarns: list[Yarn] = Field(default_factory=list)
    unmatched: list[UnmatchedYarn] = Field(default_factory=list)
    affected_keys: list[str] = Field(default_factory=list)
    affected_yarn_count: int = 0

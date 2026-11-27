"""Inputs of one costsheet: 4.12 yarn lines .. 4.17 price (what sales types; results are in costsheet_result)."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.enums import (
    Currency,
    ExtraCostType,
    FiberSystem,
    YarnDirection,
    YarnKind,
)

ZERO = Decimal(0)


class YarnLine(BaseValueObject):
    """4.12 one yarn line (taken from the fabric yarns; sales types price, waste, Se / Hồ ticks)."""

    direction: YarnDirection
    seq: int = Field(ge=1)
    yarn_name: str = ""  # raw_yarn_name (sợi gốc)
    source_yarn_name: str = ""  # yarn_name of 4.2 (used by BR-08)
    yarn_kind: YarnKind | None = None
    twist_tpm: str = ""
    ratio: Decimal = ZERO
    price_currency: Currency = Currency.USD
    price_input: Decimal | None = None
    price_vnd: Decimal = ZERO
    price_entered_on: date | None = None
    waste_rate: Decimal = Field(default=ZERO, ge=0, lt=1)
    is_twisted: bool = False
    is_sized: bool = False
    size_suggest_reason: str = ""


class TwistLine(BaseValueObject):
    """4.13 one Se line: direction (Dọc / Ngang), fiber system, count, twist, quantity.

    ``fiber_suggested``: the fiber system is the app suggestion (BR-83), refreshed when the count changes.
    ``suggested``: the whole line is still the app suggestion (BR-86, rebuilt at each calculation); False = typed or
    edited by sales (the default, so lines stored before 2026-11-23 stay as they are). ``suggestion_key``: the
    suggestion the line came from (kept after an edit so the app does not suggest it again)."""

    direction: str = "Dọc"
    fiber_system: FiberSystem | None = None
    count: str = ""
    twist: int | None = None
    quantity_kg: Decimal | None = None
    fiber_suggested: bool = False
    suggested: bool = False
    suggestion_key: str = ""


class ConeLine(BaseValueObject):
    """4.14a one cone line (2026-11-26): count, quantity, the Ngang Se lines gathered in it (``members``, read only).

    ``suggested``: the line is still the app suggestion (BR-100, rebuilt at each calculation); False = typed or edited
    by sales. ``suggestion_key``: the suggestion the line came from (kept after an edit so it is not suggested again)."""

    count: str = ""
    quantity_kg: Decimal | None = None
    members: str = ""
    suggested: bool = False
    suggestion_key: str = ""


class WeavingInput(BaseValueObject):
    """4.14 choices and outsourcing of the weaving department.

    Cone (2026-11-26): ``cone_lines`` = the cone table 4.14a, valid once ``cone_lines_converted`` is True (set by
    every calculation / screen). ``cone_lines_live``: BR-100 suggestions are made on this costsheet. The old cells
    ``cone_count_1`` .. ``cone_qty_2`` (BR-87, removed 2026-11-26) are only read to convert costsheets stored before
    (``Costsheet.cone_rows``); ``cone_*_1_suggested`` = the old cell held the BR-87 suggestion."""

    size_material: str = ""
    warping_band: str = ""  # "Có" / "Không" / ""
    cone_count_1: str = ""
    cone_qty_1: Decimal | None = None
    cone_count_1_suggested: bool = False
    cone_qty_1_suggested: bool = False
    cone_count_2: str = ""
    cone_qty_2: Decimal | None = None
    cone_lines: list[ConeLine] = Field(default_factory=list)
    cone_lines_converted: bool = False
    cone_lines_live: bool = False
    cone_suggestions: list[ConeLine] = Field(default_factory=list)  # suggested lines of the last calculation
    cone_suggestion_skips: list[str] = Field(default_factory=list)  # suggestions deleted / edited by sales
    twist_outsourcing_price: Decimal | None = None
    twist_outsourcing_qty: Decimal | None = None
    size_outsourcing_price: Decimal | None = None
    weaving_outsourcing_price: Decimal | None = None
    other_outsourcing_price: Decimal | None = None


class NamedCost(BaseValueObject):
    name: str = ""
    amount: Decimal | None = None


class ExtraCost(BaseValueObject):
    """Chi phí phát sinh do ngành báo giá: name + the 7 items (HCM: HCTN = chemical, Tiền lương = labor)."""

    name: str = ""
    items: CostItems = Field(default_factory=CostItems)


class HcmDyeingInput(BaseValueObject):
    """4.15."""

    dye_material: str = ""
    color_level: str = ""
    blend_ratios: list[Decimal] = Field(default_factory=lambda: [ZERO] * 5)
    width_type: int = Field(default=1, ge=1, le=3)
    dye_loss_rate: Decimal | None = None
    special_stages: list[str] = Field(default_factory=list)
    special_features: list[str] = Field(default_factory=list)
    special_costs: list[NamedCost] = Field(default_factory=list)
    extra_cost: ExtraCost | None = None
    extra_cost_reason: str = ""
    outsourcing_lines: list[NamedCost] = Field(default_factory=list)


class TcdnStageInput(BaseValueObject):
    name: str = ""
    chemical_price: Decimal | None = None
    repeat_count: int = Field(default=0, ge=0, le=9)  # 4.22 (2026-11-25): "số lần xử lý thêm", dyeing job only


class TcdnOutsourcing(BaseValueObject):
    name: str = ""
    amount: Decimal | None = None
    loss_rate: Decimal | None = None


class TcdnDyeingInput(BaseValueObject):
    """4.16."""

    dye_material: str = ""
    color_level: str = ""
    blend_ratios: list[Decimal] = Field(default_factory=lambda: [ZERO] * 5)
    special_dye: str = ""
    special_dye_chemical_price: Decimal | None = None
    wr_chemical: str = ""
    extra_stages: list[TcdnStageInput] = Field(default_factory=list)
    special_features: list[NamedCost] = Field(default_factory=list)
    extra_cost_type: ExtraCostType | None = None
    extra_cost_loss_rate: Decimal | None = None
    extra_cost: ExtraCost | None = None
    extra_cost_reason: str = ""
    outsourcing_lines: list[TcdnOutsourcing] = Field(default_factory=list)


class CogsLine(BaseValueObject):
    name: str = ""
    amount: Decimal | None = None
    note: str = ""


class PriceInput(BaseValueObject):
    """4.17."""

    sell_price_currency: Currency = Currency.USD
    sell_price_input: Decimal | None = None
    cogs_extra_lines: list[CogsLine] = Field(default_factory=list)
    commission: Decimal = ZERO
    freight_insurance: Decimal = ZERO
    interest_cost: Decimal = ZERO
    ship_date: date | None = None

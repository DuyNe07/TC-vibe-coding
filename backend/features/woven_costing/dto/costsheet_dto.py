"""DTOs of the costsheet use cases UC-14..UC-25 and UC-29 (Screen 2)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.woven_costing.dto.common_dto import WarningDTO
from backend.features.woven_costing.dto.fabric_dto import FabricSpecsDTO, FabricYarnDTO
from backend.features.woven_costing.dto.master_dto import ParameterValueDTO
from backend.features.woven_costing.models.enums import (
    CostsheetAction,
    CostsheetStatus,
    Currency,
    DyePlant,
    ExtraCostType,
    FabricSource,
    FiberSystem,
    HistoryAction,
    Market,
    OrderType,
    PriceType,
    SaleForm,
    ShrinkageException,
    YarnDirection,
)

ZERO = Decimal(0)


# ---- inputs -------------------------------------------------------------------------------------------------------
class YarnLineInputDTO(BaseDTO):
    direction: YarnDirection
    seq: int
    price_currency: Currency = Currency.USD
    price_input: Decimal | None = None
    waste_rate: Decimal | None = None
    is_twisted: bool = False
    is_sized: bool = False


class TwistLineDTO(BaseDTO):
    """4.13 one Se line; ``fiber_suggested`` = the fiber system is still the app suggestion (BR-83)."""

    direction: str = "Dọc"
    fiber_system: FiberSystem | None = None
    count: str = ""
    twist: int | None = None
    quantity_kg: Decimal | None = None
    fiber_suggested: bool = False
    suggested: bool = False  # BR-86: the line is still the app suggestion
    suggestion_key: str = ""


class ConeLineDTO(BaseDTO):
    """4.14a one cone line (2026-11-26); ``suggested`` = still the app suggestion (BR-100)."""

    count: str = ""
    quantity_kg: Decimal | None = None
    members: str = ""
    suggested: bool = False
    suggestion_key: str = ""


class WeavingInputDTO(BaseDTO):
    """4.14; cone table 4.14a in ``cone_lines`` (the old cells cone 1 / cone 2 are only read for stored costsheets)."""

    size_material: str = ""
    warping_band: str = ""
    cone_count_1: str = ""
    cone_qty_1: Decimal | None = None
    cone_count_1_suggested: bool = False
    cone_qty_1_suggested: bool = False
    cone_count_2: str = ""
    cone_qty_2: Decimal | None = None
    cone_lines: list[ConeLineDTO] = Field(default_factory=list)
    cone_lines_converted: bool = False
    cone_lines_live: bool = False
    cone_suggestions: list[ConeLineDTO] = Field(default_factory=list)
    cone_suggestion_skips: list[str] = Field(default_factory=list)
    twist_outsourcing_price: Decimal | None = None
    twist_outsourcing_qty: Decimal | None = None
    size_outsourcing_price: Decimal | None = None
    weaving_outsourcing_price: Decimal | None = None
    other_outsourcing_price: Decimal | None = None


class NamedCostDTO(BaseDTO):
    name: str = ""
    amount: Decimal | None = None


class ExtraCostDTO(BaseDTO):
    """HCM: HCTN = chemical, Tiền lương = labor, Quản lý = overhead."""

    name: str = ""
    chemical: Decimal | None = None
    labor: Decimal | None = None
    depreciation: Decimal | None = None
    power: Decimal | None = None
    fuel: Decimal | None = None
    material: Decimal | None = None
    overhead: Decimal | None = None


class HcmDyeingInputDTO(BaseDTO):
    dye_material: str = ""
    color_level: str = ""
    blend_ratios: list[Decimal] = Field(default_factory=lambda: [ZERO] * 5)
    width_type: int = 1
    dye_loss_rate: Decimal | None = None
    special_stages: list[str] = Field(default_factory=list)
    special_features: list[str] = Field(default_factory=list)
    special_costs: list[NamedCostDTO] = Field(default_factory=list)
    extra_cost: ExtraCostDTO | None = None
    extra_cost_reason: str = ""
    outsourcing_lines: list[NamedCostDTO] = Field(default_factory=list)


class TcdnStageInputDTO(BaseDTO):
    name: str = ""
    chemical_price: Decimal | None = None
    repeat_count: int = 0  # "số lần xử lý thêm" (dyeing job order only, 2026-11-25)


class TcdnOutsourcingDTO(BaseDTO):
    name: str = ""
    amount: Decimal | None = None
    loss_rate: Decimal | None = None


class TcdnDyeingInputDTO(BaseDTO):
    dye_material: str = ""
    color_level: str = ""
    blend_ratios: list[Decimal] = Field(default_factory=lambda: [ZERO] * 5)
    special_dye: str = ""
    special_dye_chemical_price: Decimal | None = None
    wr_chemical: str = ""
    extra_stages: list[TcdnStageInputDTO] = Field(default_factory=list)
    special_features: list[NamedCostDTO] = Field(default_factory=list)
    extra_cost_type: ExtraCostType | None = None
    extra_cost_loss_rate: Decimal | None = None
    extra_cost: ExtraCostDTO | None = None
    extra_cost_reason: str = ""
    outsourcing_lines: list[TcdnOutsourcingDTO] = Field(default_factory=list)


class CogsLineDTO(BaseDTO):
    name: str = ""
    amount: Decimal | None = None
    note: str = ""


class PriceInputDTO(BaseDTO):
    sell_price_currency: Currency = Currency.USD
    sell_price_input: Decimal | None = None
    cogs_extra_lines: list[CogsLineDTO] = Field(default_factory=list)
    commission: Decimal | None = None
    freight_insurance: Decimal | None = None
    interest_cost: Decimal | None = None
    ship_date: date | None = None


class ParameterOverrideDTO(BaseDTO):
    code: str
    used_value: Decimal


class CostsheetInputDTO(BaseDTO):
    """Every cell sales type on Screen 2 (same field names as CostsheetInputRequest)."""

    dye_plant: DyePlant = DyePlant.HCM
    customer_name: str = ""
    market: Market | None = None
    order_type: OrderType | None = None
    style: str = ""
    sale_form: SaleForm | None = None
    greige_buy_price: Decimal | None = None
    delivery_date: date | None = None
    costing_date: date | None = None
    tcfno: str = ""
    order_meters: Decimal | None = None
    price_type: PriceType | None = None
    oc_no: str = ""
    shrinkage_exception: ShrinkageException = ShrinkageException.NONE
    shrinkage_reason: str = ""
    note: str = ""
    yarn_lines: list[YarnLineInputDTO] = Field(default_factory=list)
    twist_lines: list[TwistLineDTO] = Field(default_factory=list)
    twist_lines_suggested: bool = False  # BR-86: the app has suggested Se lines on this costsheet
    twist_lines_live: bool = False  # BR-86: suggested Se lines follow the Se ticks (costsheets from 2026-11-23)
    twist_suggestions: list[TwistLineDTO] = Field(default_factory=list)  # suggested lines of the last calculation
    twist_suggestion_skips: list[str] = Field(default_factory=list)  # suggestions deleted / edited by sales
    weaving: WeavingInputDTO = Field(default_factory=WeavingInputDTO)
    hcm_dyeing: HcmDyeingInputDTO = Field(default_factory=HcmDyeingInputDTO)
    tcdn_dyeing: TcdnDyeingInputDTO = Field(default_factory=TcdnDyeingInputDTO)
    price: PriceInputDTO = Field(default_factory=PriceInputDTO)
    parameter_overrides: list[ParameterOverrideDTO] = Field(default_factory=list)


class CostsheetInputRequest(BaseRequestDTO, CostsheetInputDTO):
    """UC-16 / UC-17 (and UC-20 through CostsheetActionRequest.input)."""

    costsheet_id: str | None = None
    confirm_yarn_prices: bool = False


class CreateCostsheetRequest(BaseRequestDTO):
    dye_plant: DyePlant = DyePlant.HCM
    customer_name: str = ""
    market: Market | None = None
    order_type: OrderType | None = None
    style: str = ""
    sale_form: SaleForm | None = None
    greige_buy_price: Decimal | None = None
    delivery_date: date | None = None
    costing_date: date | None = None
    tcfno: str = ""
    order_meters: Decimal | None = None
    price_type: PriceType | None = None
    oc_no: str = ""


class CostsheetActionRequest(BaseRequestDTO):
    costsheet_id: str
    reason: str | None = None
    input: CostsheetInputRequest | None = None


class SaveOcRequest(BaseRequestDTO):
    costsheet_id: str
    oc_no: str = ""
    close_order: bool = False


class GetCostsheetRequest(BaseRequestDTO):
    costsheet_id: str | None = None
    costsheet_no: str | None = None
    version: int | None = None


class UpdateFabricOverrideRequest(BaseRequestDTO):
    costsheet_id: str
    specs: FabricSpecsDTO = Field(default_factory=FabricSpecsDTO)
    yarns: list[FabricYarnDTO] = Field(default_factory=list)


# ---- outputs ------------------------------------------------------------------------------------------------------
class FabricSnapshotDTO(FabricSpecsDTO):
    tcfno: str
    fabric_name: str = ""
    source: FabricSource = FabricSource.MANUAL
    greige_m_per_kg: Decimal = ZERO
    finished_m_per_kg: Decimal = ZERO
    overridden_fields: list[str] = Field(default_factory=list)
    yarns: list[FabricYarnDTO] = Field(default_factory=list)


class YarnLineViewDTO(BaseDTO):
    direction: YarnDirection
    seq: int
    yarn_name: str = ""
    twist_tpm: str = ""
    ratio: Decimal = ZERO
    price_currency: Currency = Currency.USD
    price_input: Decimal | None = None
    price_vnd: Decimal = ZERO
    price_entered_on: date | None = None
    price_expired: bool = False
    waste_rate: Decimal = ZERO
    is_twisted: bool = False
    is_sized: bool = False
    size_suggest_reason: str = ""
    loss_rate: Decimal = ZERO
    yarn_kg: Decimal = ZERO
    amount: Decimal = ZERO


class StageCostDTO(BaseDTO):
    """One stage line: ``amount`` = quantity x norm (before the quantity factor), ``amount_after_factor`` = what
    counts in the weaving total (x quantity factor when ``applies_quantity_factor``, BR-23)."""

    stage: str
    quantity: Decimal = ZERO
    unit: str = ""
    norm: Decimal = ZERO
    factor_applied: Decimal = Decimal(1)
    amount: Decimal = ZERO
    applies_quantity_factor: bool = False
    amount_after_factor: Decimal = ZERO


class CostItemRowDTO(BaseDTO):
    stage: str
    labor: Decimal = ZERO
    depreciation: Decimal = ZERO
    power: Decimal = ZERO
    material: Decimal = ZERO
    fuel: Decimal = ZERO
    chemical: Decimal = ZERO
    overhead: Decimal = ZERO
    total: Decimal = ZERO


class DyeingLineDTO(BaseDTO):
    group: str = ""
    name: str
    chemical: Decimal = ZERO
    labor: Decimal = ZERO
    depreciation: Decimal = ZERO
    power: Decimal = ZERO
    fuel: Decimal = ZERO
    material: Decimal = ZERO
    overhead: Decimal = ZERO
    factor: Decimal = Decimal(1)
    loss_rate: Decimal = ZERO
    per_kg: Decimal = ZERO
    per_m: Decimal = ZERO
    note: str = ""


class TwistLineResultDTO(BaseDTO):
    direction: str
    count: str = ""
    quantity_kg: Decimal = ZERO
    norm: Decimal = ZERO
    amount: Decimal = ZERO
    error: str = ""


class ProfitRowDTO(BaseDTO):
    label: str
    vnd: Decimal | None = None
    usd: Decimal | None = None
    is_percent: bool = False
    below_threshold: bool = False


class DemandStepDTO(BaseDTO):
    """One row of the "Chuỗi nhu cầu" block (read-only, worked back from the finished meters sold)."""

    step: str
    meters: Decimal | None = None
    kg: Decimal | None = None
    losses: str = ""
    cost: Decimal | None = None  # đ; B/C liquidation is negative
    cost_per_m: Decimal | None = None  # cost / order meters
    is_total: bool = False


class CostsheetResultDTO(BaseDTO):
    calculated: bool = False
    greige_meters: Decimal = ZERO
    finished_meters_needed: Decimal = ZERO
    greige_kg: Decimal = ZERO
    finished_kg: Decimal = ZERO
    quantity_factor: Decimal = ZERO
    quantity_factor_reason: str = ""  # BR-23 why this factor ("Thí Nghiệm", "12.720 m mộc", ...)
    shrinkage: Decimal = ZERO
    low_shrinkage: bool = False
    dye_loss_rate: Decimal = ZERO
    greige_bc_rate: Decimal = ZERO
    finished_bc_rate: Decimal = ZERO
    yarn_ratio_total: Decimal = ZERO
    yarn_total: Decimal = ZERO
    twist_estimated_kg: Decimal = ZERO
    twist_entered_kg: Decimal = ZERO
    twist_difference_kg: Decimal = ZERO
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
    unit_cost_usd: Decimal = ZERO
    cogs_vnd: Decimal = ZERO
    cogs_usd: Decimal = ZERO
    sell_price_vnd: Decimal = ZERO
    sell_price_usd: Decimal = ZERO
    gp: Decimal = ZERO
    gp_pct: Decimal = ZERO
    sa: Decimal = ZERO
    op: Decimal = ZERO
    op_pct: Decimal = ZERO
    price_with_vat: Decimal = ZERO
    gp_threshold: Decimal = ZERO
    op_threshold: Decimal = ZERO
    gp_below: bool = False
    op_below: bool = False
    twist_lines: list[TwistLineResultDTO] = Field(default_factory=list)
    weaving_stages: list[StageCostDTO] = Field(default_factory=list)
    cost_items: list[CostItemRowDTO] = Field(default_factory=list)
    dyeing_lines: list[DyeingLineDTO] = Field(default_factory=list)
    profit_rows: list[ProfitRowDTO] = Field(default_factory=list)
    demand_chain: list[DemandStepDTO] = Field(default_factory=list)


class VersionDTO(BaseDTO):
    id: str
    version: int
    status: CostsheetStatus
    costing_date: date
    sell_price_vnd: Decimal = ZERO
    cogs_vnd: Decimal = ZERO
    gp_pct: Decimal = ZERO
    approved_by_name: str = ""
    approved_at: datetime | None = None


class HistoryDTO(BaseDTO):
    version: int
    action: HistoryAction
    by_name: str = ""
    at: datetime
    comment: str = ""


class CostsheetResponse(BaseResponseDTO):
    id: str = ""
    costsheet_no: str = ""
    version: int = 1
    status: CostsheetStatus = CostsheetStatus.NHAP
    editable: bool = False
    allowed_actions: list[CostsheetAction] = Field(default_factory=list)
    message: str = ""
    warnings: list[WarningDTO] = Field(default_factory=list)
    warning_texts: list[str] = Field(default_factory=list)
    auto_approved: bool = False
    saved: bool = True
    sales_username: str = ""
    sales_name: str = ""
    team: str = ""
    approved_by_name: str = ""
    approved_at: datetime | None = None
    return_reason: str = ""
    cancel_reason: str = ""
    copied_from: str = ""
    exchange_rate: Decimal = ZERO
    norm_set_code: str = ""
    parameter_set_date: date | None = None
    fabric_overridden: bool = False
    size_suggest_reason: str = ""
    input: CostsheetInputDTO = Field(default_factory=CostsheetInputDTO)
    fabric: FabricSnapshotDTO | None = None
    yarn_lines: list[YarnLineViewDTO] = Field(default_factory=list)
    result: CostsheetResultDTO = Field(default_factory=CostsheetResultDTO)
    parameters: list[ParameterValueDTO] = Field(default_factory=list)
    versions: list[VersionDTO] = Field(default_factory=list)
    history: list[HistoryDTO] = Field(default_factory=list)

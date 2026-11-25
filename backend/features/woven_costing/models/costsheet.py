"""4.11 Costsheet (one record per version) with its snapshot, inputs, overrides and stored results; 4.19 history."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.woven_costing.models.costsheet_input import (
    HcmDyeingInput,
    PriceInput,
    TcdnDyeingInput,
    TwistLine,
    WeavingInput,
    YarnLine,
)
from backend.features.woven_costing.models.costsheet_result import CostsheetResult
from backend.features.woven_costing.models.enums import (
    CostsheetStatus,
    DyePlant,
    FabricSource,
    HistoryAction,
    Market,
    OrderType,
    PriceType,
    SaleForm,
    ShrinkageException,
)
from backend.features.woven_costing.models.fabric import FabricSpecs, FabricYarn
from backend.features.woven_costing.models.parameter_set import ParameterOverride

EDITABLE_STATUSES = (CostsheetStatus.NHAP, CostsheetStatus.TRA_LAI)
OPEN_STATUSES = (CostsheetStatus.NHAP, CostsheetStatus.CHO_DUYET, CostsheetStatus.TRA_LAI)
APPROVED_STATUSES = (CostsheetStatus.DA_DUYET, CostsheetStatus.DA_CHOT_DON)


class FabricSnapshot(BaseValueObject):
    """Snapshot of 4.1 + 4.2 used by the calculation (kept with the version)."""

    tcfno: str
    fabric_name: str = ""
    source: FabricSource = FabricSource.MANUAL
    specs: FabricSpecs = Field(default_factory=FabricSpecs)
    yarns: list[FabricYarn] = Field(default_factory=list)
    overridden_fields: list[str] = Field(default_factory=list)


class Costsheet(BaseEntity):
    costsheet_no: str
    version: int = Field(default=1, ge=1)
    status: CostsheetStatus = CostsheetStatus.NHAP
    copied_from: str = ""
    dye_plant: DyePlant = DyePlant.HCM
    customer_name: str = ""
    market: Market | None = None
    order_type: OrderType | None = None
    oc_no: str = ""
    style: str = Field(default="", max_length=100)
    sale_form: SaleForm | None = None
    greige_buy_price: Decimal | None = None
    delivery_date: date | None = None
    sales_username: str = ""
    sales_name: str = ""
    team: str = ""
    costing_date: date
    tcfno: str
    order_meters: Decimal | None = None
    exchange_rate: Decimal = Decimal(0)
    norm_set_code: str = ""
    parameter_set_date: date | None = None
    fabric_snapshot: FabricSnapshot
    fabric_overridden: bool = False
    shrinkage_exception: ShrinkageException = ShrinkageException.NONE
    shrinkage_reason: str = Field(default="", max_length=300)
    price_type: PriceType | None = None
    note: str = Field(default="", max_length=1000)
    return_reason: str = ""
    cancel_reason: str = ""
    approved_by: str = ""
    approved_by_name: str = ""
    approved_at: datetime | None = None
    created_by: str = ""
    yarn_lines: list[YarnLine] = Field(default_factory=list)
    twist_lines: list[TwistLine] = Field(default_factory=list)
    twist_lines_suggested: bool = False  # BR-86: the app has suggested Se lines on this costsheet
    # BR-86 (2026-11-23): suggested Se lines follow the Se ticks; False on costsheets stored before (lines kept as is)
    twist_lines_live: bool = False
    twist_suggestions: list[TwistLine] = Field(default_factory=list)  # suggested lines of the last calculation
    twist_suggestion_skips: list[str] = Field(default_factory=list)  # suggestions deleted / edited by sales
    weaving: WeavingInput = Field(default_factory=WeavingInput)
    hcm_dyeing: HcmDyeingInput = Field(default_factory=HcmDyeingInput)
    tcdn_dyeing: TcdnDyeingInput = Field(default_factory=TcdnDyeingInput)
    price: PriceInput = Field(default_factory=PriceInput)
    parameter_overrides: list[ParameterOverride] = Field(default_factory=list)
    result: CostsheetResult = Field(default_factory=CostsheetResult)

    @property
    def is_editable_status(self) -> bool:
        return self.status in EDITABLE_STATUSES

    @property
    def label(self) -> str:
        return f"{self.costsheet_no} v{self.version}"


class CostsheetHistory(BaseEntity):
    """4.19 one action on a costsheet version."""

    costsheet_no: str
    version: int
    action: HistoryAction
    by: str = ""
    by_name: str = ""
    comment: str = ""

"""DTOs of UC-27 / UC-28 (costsheet list, export), UC-30 (my tasks), UC-38 (options), UC-18 (add customer)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.woven_costing.models.enums import (
    CostsheetStatus,
    DyePlant,
    Market,
    OrderType,
    PriceType,
    SaleForm,
)


class ListCostsheetsRequest(BaseRequestDTO):
    keyword: str = ""
    statuses: list[CostsheetStatus] = Field(default_factory=list)
    team: str | None = None
    sales_username: str | None = None
    customer_name: str | None = None
    dye_plant: DyePlant | None = None
    order_type: OrderType | None = None
    price_type: PriceType | None = None
    date_from: date | None = None
    date_to: date | None = None
    latest_only: bool = True
    below_threshold_only: bool = False


class CostsheetListRowDTO(BaseDTO):
    id: str
    costsheet_no: str
    version: int
    status: CostsheetStatus
    costing_date: date
    sales_name: str = ""
    team: str = ""
    customer_name: str = ""
    market: Market | None = None
    order_type: OrderType | None = None
    oc_no: str = ""
    tcfno: str = ""
    sale_form: SaleForm | None = None
    dye_plant: DyePlant
    price_type: PriceType | None = None
    order_meters: Decimal | None = None
    sell_price_vnd: Decimal = Decimal(0)
    sell_price_usd: Decimal = Decimal(0)
    cogs_vnd: Decimal = Decimal(0)
    freight_insurance: Decimal = Decimal(0)
    gp_pct: Decimal = Decimal(0)
    op_pct: Decimal = Decimal(0)
    warning_text: str = ""
    approved_by_name: str = ""
    approved_at: datetime | None = None


class CostsheetKpiDTO(BaseDTO):
    total: int = 0
    pending: int = 0
    approved: int = 0
    closed: int = 0
    below_threshold: int = 0
    low_shrinkage: int = 0


class CostsheetListResponse(BaseResponseDTO):
    rows: list[CostsheetListRowDTO] = Field(default_factory=list)
    kpis: CostsheetKpiDTO = Field(default_factory=CostsheetKpiDTO)


class TaskRowDTO(BaseDTO):
    costsheet_id: str | None = None
    costsheet_no: str | None = None
    version: int | None = None
    customer_name: str | None = None
    tcfno: str | None = None
    sales_name: str | None = None
    costing_date: date | None = None
    gp_pct: Decimal | None = None
    op_pct: Decimal | None = None
    reason: str | None = None


class TaskGroupDTO(BaseDTO):
    code: str
    title: str
    kind: str = "costsheet"
    rows: list[TaskRowDTO] = Field(default_factory=list)


class MyTasksResponse(BaseResponseDTO):
    groups: list[TaskGroupDTO] = Field(default_factory=list)


class CustomerOptionDTO(BaseDTO):
    name: str
    customer_code: str
    team: str


class UserOptionDTO(BaseDTO):
    username: str
    name: str
    team: str = ""


class CountOptionDTO(BaseDTO):
    fiber_system: str
    count: str


class CostsheetOptionsResponse(BaseResponseDTO):
    customers: list[CustomerOptionDTO] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)
    sales_users: list[UserOptionDTO] = Field(default_factory=list)
    counts: list[CountOptionDTO] = Field(default_factory=list)
    twists: list[int] = Field(default_factory=list)
    size_materials: list[str] = Field(default_factory=list)
    hcm_dye_materials: list[str] = Field(default_factory=list)
    hcm_color_levels: list[str] = Field(default_factory=list)
    hcm_special_stages: list[str] = Field(default_factory=list)
    hcm_special_features: list[str] = Field(default_factory=list)
    tcdn_dye_materials: list[str] = Field(default_factory=list)
    tcdn_color_levels: list[str] = Field(default_factory=list)
    tcdn_stages: list[str] = Field(default_factory=list)
    special_dyes: list[str] = Field(default_factory=list)
    wr_chemicals: list[str] = Field(default_factory=list)
    my_roles: list[str] = Field(default_factory=list)
    my_team: str | None = None


class AddCustomerRequest(BaseRequestDTO):
    name: str
    customer_code: str | None = None
    confirm_new: bool = False


class AddCustomerResponse(BaseResponseDTO):
    created: bool = False
    customer_name: str = ""
    customer_code: str = ""
    suggested_code: str = ""
    similar: list[CustomerOptionDTO] = Field(default_factory=list)
    message: str = ""

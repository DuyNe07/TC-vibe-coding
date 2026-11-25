"""DTOs of the Phòng SO data: rates (UC-05, UC-31), norm sets (UC-06..UC-08, UC-37), parameters (UC-09, UC-32),
fabric factors (UC-10, UC-33), holidays (UC-11, UC-34), customers (UC-12, UC-13, UC-35, UC-36)."""

import datetime as dt
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import Field

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, UploadedFileDTO
from backend.features.woven_costing.models.enums import (
    CostItem,
    CustomerImportResult,
    CustomerTeam,
    DiscountCondition,
    DiscountDepartment,
    FactorStage,
    HolidayAction,
    ParamGroup,
    QuantityUnit,
    SaleForm,
)


class SaveExchangeRateRequest(BaseRequestDTO):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2020, le=2100)
    rate: Decimal


class ExchangeRateDTO(BaseDTO):
    month: int
    year: int
    rate: Decimal
    updated_by: str = ""
    updated_at: datetime


class ExchangeRateListResponse(BaseResponseDTO):
    rows: list[ExchangeRateDTO] = Field(default_factory=list)


class SaveNormSetRequest(BaseRequestDTO):
    file: UploadedFileDTO
    effective_from: date
    note: str = Field(default="", max_length=300)


class SaveNormSetResponse(BaseResponseDTO):
    norm_set_code: str
    message: str


class SheetCountDTO(BaseDTO):
    sheet: str
    rows: int


class NormChangeDTO(BaseDTO):
    sheet: str
    key: str
    column: str
    old_value: str = ""
    new_value: str = ""


class NormSetPreviewResponse(BaseResponseDTO):
    sheet_counts: list[SheetCountDTO] = Field(default_factory=list)  # the 12 required sheets
    optional_sheet_counts: list[SheetCountDTO] = Field(default_factory=list)  # sheet `Spandex` when present
    changes: list[NormChangeDTO] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ViewNormSetRequest(BaseRequestDTO):
    norm_set_code: str | None = None


class NormSetRowDTO(BaseDTO):
    norm_set_code: str
    effective_from: date
    note: str = ""
    uploaded_by: str = ""
    uploaded_at: datetime
    is_current: bool = False


class NormTableDTO(BaseDTO):
    sheet: str
    title: str
    group: str = ""  # Screen 5 sub-tab: Dệt / Nhuộm HCM / Nhuộm TCDN / Danh mục chọn
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class NormSetDetailDTO(BaseDTO):
    norm_set_code: str
    tables: list[NormTableDTO] = Field(default_factory=list)  # the 12 tables of F-05
    optional_tables: list[NormTableDTO] = Field(default_factory=list)  # 4.5.13 "Spandex cộng thêm"


class NormSetResponse(BaseResponseDTO):
    sets: list[NormSetRowDTO] = Field(default_factory=list)
    selected: NormSetDetailDTO | None = None


class ParameterValueDTO(BaseDTO):
    code: str
    label: str
    unit: str = ""
    is_percent: bool = False
    so_only: bool = False
    default_value: Decimal
    used_value: Decimal
    group: ParamGroup = ParamGroup.PRICE  # 2026-11-25: department (sub-tab / group of block G)
    reason: str = ""  # applied discount / % B/C: the row of the table it comes from


class ParameterValueInputDTO(BaseDTO):
    code: str
    value: Decimal


class DiscountRowDTO(BaseDTO):
    """4.6.1 one row of the quantity discount table."""

    department: DiscountDepartment
    condition: DiscountCondition
    from_qty: Decimal | None = None
    from_inclusive: bool = True
    to_qty: Decimal | None = None
    to_inclusive: bool = False
    factor: Decimal
    interpolate: bool = False
    quantity_unit: QuantityUnit | None = None  # filled by the app from the department
    applies_to: str = ""  # filled by the app from the department
    reason: str = ""  # range text, e.g. "Đại trà 5.000 ≤ SL < 10.000 m mộc"


class BcRowDTO(BaseDTO):
    """4.6.2 one row of the % B/C table."""

    sale_form: SaleForm
    greige_bc_rate: Decimal
    finished_bc_rate: Decimal


class OpRateRowDTO(BaseDTO):
    """4.24 one row of the TCDN operation rate table (2026-11-25)."""

    stage: str
    rate: Decimal


class SaveParameterSetRequest(BaseRequestDTO):
    effective_from: date
    values: list[ParameterValueInputDTO] = Field(default_factory=list)
    discount_rows: list[DiscountRowDTO] | None = None  # None = the rows of the latest set
    bc_rows: list[BcRowDTO] | None = None  # None = the rows of the latest set
    op_rates: list[OpRateRowDTO] | None = None  # None = the rows of the latest set


class ParameterSetRowDTO(BaseDTO):
    effective_from: date
    created_by: str = ""
    created_at: datetime


class ParameterSetDetailDTO(BaseDTO):
    """One parameter set: single values (grouped by department) and its two tables."""

    effective_from: date
    created_by: str = ""
    values: list[ParameterValueDTO] = Field(default_factory=list)
    discount_rows: list[DiscountRowDTO] = Field(default_factory=list)
    bc_rows: list[BcRowDTO] = Field(default_factory=list)
    op_rates: list[OpRateRowDTO] = Field(default_factory=list)
    from_old_values: bool = False  # set stored before 2026-11-25: tables read from its old single values


class ParameterSetListResponse(BaseResponseDTO):
    sets: list[ParameterSetRowDTO] = Field(default_factory=list)
    latest: list[ParameterValueDTO] = Field(default_factory=list)
    details: list[ParameterSetDetailDTO] = Field(default_factory=list)  # same order as ``sets`` (latest first)


class SaveFabricFactorRequest(BaseRequestDTO):
    id: str | None = None
    tcfno: str
    stage: FactorStage
    cost_item: CostItem
    multiplier: Decimal = Decimal(1)
    addition: Decimal = Decimal(0)
    effective_from: date
    active: bool = True
    note: str = Field(default="", max_length=300)


class FabricFactorDTO(BaseDTO):
    id: str
    tcfno: str
    stage: FactorStage
    cost_item: CostItem
    multiplier: Decimal
    addition: Decimal
    effective_from: date
    active: bool
    note: str = ""


class FabricFactorListResponse(BaseResponseDTO):
    rows: list[FabricFactorDTO] = Field(default_factory=list)


class SaveHolidayRequest(BaseRequestDTO):
    action: HolidayAction = HolidayAction.ADD
    date: dt.date
    name: str = ""


class HolidayDTO(BaseDTO):
    date: dt.date
    name: str


class HolidayListResponse(BaseResponseDTO):
    rows: list[HolidayDTO] = Field(default_factory=list)


class CustomerImportRequest(BaseRequestDTO):
    file: UploadedFileDTO


class CustomerImportRowDTO(BaseDTO):
    name: str
    customer_code: str
    team: str
    result: CustomerImportResult


class CustomerImportResponse(BaseResponseDTO):
    added: int = 0
    skipped: int = 0
    rows: list[CustomerImportRowDTO] = Field(default_factory=list)
    message: str = ""


class UpdateCustomerRequest(BaseRequestDTO):
    id: str
    name: str
    customer_code: str
    team: CustomerTeam
    active: bool = True


class ListCustomersRequest(BaseRequestDTO):
    keyword: str = ""


class CustomerDTO(BaseDTO):
    id: str
    customer_code: str
    name: str
    team: CustomerTeam
    created_by: str = ""
    created_at: datetime
    active: bool = True


class CustomerListResponse(BaseResponseDTO):
    rows: list[CustomerDTO] = Field(default_factory=list)

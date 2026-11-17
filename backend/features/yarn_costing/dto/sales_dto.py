"""DTOs of UC-49..UC-54 (mở rộng 2026-11-10): gợi ý sợi, tên theo khách, so sánh 2 sợi, đối chiếu giá kế toán."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, FileDownloadDTO, UploadedFileDTO
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, YarnStatus


# ---- UC-49 / UC-50 ----
class SuggestYarnsRequest(BaseRequestDTO):
    yarn_name: str = ""
    factory_code: FactoryCode | None = None


class YarnSuggestionDTO(BaseDTO):
    kind: str  # "Trùng" / "Gần giống"
    factory_code: FactoryCode
    yarn_code: str
    yarn_name: str
    customer_names_text: str = ""
    note: str = ""  # Khác ở đâu / trùng tên theo khách
    status: YarnStatus
    total_vnd: Decimal | None = None
    usd_per_kg: Decimal | None = None
    accounting_code: str = ""


class YarnSuggestionResponse(BaseResponseDTO):
    readable: bool = False
    blend_text: str = ""
    message: str = ""
    same: list[YarnSuggestionDTO] = []
    near: list[YarnSuggestionDTO] = []
    same_in_factory: list[str] = []  # BR-78: Trùng codes in the chosen factory


class UseExistingYarnRequest(BaseRequestDTO):
    yarn_code: str
    typed_name: str = ""
    customer_name: str = ""


class SimpleLineDTO(BaseDTO):
    line_code: str
    line_type: LineType
    total_vnd: Decimal
    usd_per_kg: Decimal | None = None
    accounting_code: str = ""


class UseExistingYarnResponse(BaseResponseDTO):
    message: str
    saved: bool = False
    yarn_code: str = ""
    yarn_name: str = ""
    lines: list[SimpleLineDTO] = []


# ---- UC-51 ----
class CustomerNameDTO(BaseDTO):
    id: str
    base_code: str
    customer_name: str
    customer_yarn_name: str
    note: str = ""
    created_by: str = ""
    created_at: datetime | None = None
    updated_by: str = ""


class ListCustomerNamesRequest(BaseRequestDTO):
    base_code: str = ""  # empty = every customer name (options of the Khách hàng filter)


class CustomerNameListResponse(BaseResponseDTO):
    items: list[CustomerNameDTO] = []


class SaveCustomerNameRequest(BaseRequestDTO):
    """UC-51: add (alias_id None), edit (alias_id + new values) or delete (alias_id + delete=True)."""

    base_code: str
    customer_name: str = ""
    customer_yarn_name: str = ""
    note: str = ""
    alias_id: str | None = None
    delete: bool = False


class CustomerNameResponse(BaseResponseDTO):
    message: str
    item: CustomerNameDTO | None = None


# ---- UC-52 ----
class ComparePriceLinesRequest(BaseRequestDTO):
    line_a: str
    line_b: str


class CompareInfoRowDTO(BaseDTO):
    label: str
    a: str = ""
    b: str = ""


class ComparePriceRowDTO(BaseDTO):
    label: str
    a: Decimal | None = None
    b: Decimal | None = None
    difference: Decimal | None = None
    difference_percent: Decimal | None = None


class CompareStageRowDTO(BaseDTO):
    stage_code: str
    stage_name: str = ""
    nsm_a: Decimal | None = None
    nsm_b: Decimal | None = None
    loss_a: Decimal | None = None
    loss_b: Decimal | None = None
    cost_a: Decimal | None = None
    cost_b: Decimal | None = None


class ComparePriceLinesResponse(BaseResponseDTO):
    info: list[CompareInfoRowDTO] = []
    prices: list[ComparePriceRowDTO] = []
    stages: list[CompareStageRowDTO] = []


# ---- UC-53 ----
class ImportAccountingFileRequest(BaseRequestDTO):
    file: UploadedFileDTO
    commit: bool = False


class AccountingMonthCheckDTO(BaseDTO):
    period: str
    sheet: str
    s1_count: int = 0
    s4_count: int = 0
    total_quantity: Decimal = Decimal(0)
    rejected_count: int = 0
    note: str = ""


class AccountingImportResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    valid_count: int = 0
    months: list[AccountingMonthCheckDTO] = []
    rejected_rows: list[RejectedRowDTO] = []
    result_file: FileDownloadDTO | None = None


class ListAccountingMonthsRequest(BaseRequestDTO):
    pass


class AccountingMonthDTO(BaseDTO):
    id: str
    period: str
    file_name: str = ""
    sheet_name: str = ""
    row_count: int = 0
    total_quantity: Decimal = Decimal(0)
    imported_by: str = ""
    imported_at: datetime | None = None


class AccountingMonthListResponse(BaseResponseDTO):
    items: list[AccountingMonthDTO] = []


# ---- UC-54 ----
class GetAccountingComparisonRequest(BaseRequestDTO):
    period: str
    factory_code: FactoryCode | None = None
    small_kg: Decimal = Decimal(100)
    gap_percent: Decimal = Decimal(10)
    only_gap: bool = False
    hide_small: bool = False


class AccountingCompareRowDTO(BaseDTO):
    factory_code: FactoryCode
    accounting_code: str
    product_name: str = ""
    line_code: str = ""
    yarn_name: str = ""
    quantity: Decimal
    app_total: Decimal
    app_price_date: date | None = None
    app_price_note: str = ""  # "giá hiện tại" / "Mã kế toán có ở n dòng giá"
    accounting_conversion: Decimal
    difference: Decimal
    difference_percent: Decimal | None = None
    app_labor: Decimal
    app_depreciation: Decimal
    app_electricity: Decimal
    app_materials: Decimal
    app_overhead: Decimal
    kt_labor: Decimal
    kt_depreciation: Decimal
    kt_power: Decimal
    kt_materials: Decimal
    kt_overhead: Decimal
    accounting_unit_cost: Decimal
    warnings: list[str] = []


class AccountingMissingRowDTO(BaseDTO):
    factory_code: FactoryCode
    accounting_code: str
    product_name: str = ""
    quantity: Decimal
    accounting_conversion: Decimal


class AccountingComparisonResponse(BaseResponseDTO):
    period: str = ""
    matched_count: int = 0
    gap_count: int = 0
    small_count: int = 0
    missing_count: int = 0
    weighted_gap_percent: Decimal | None = None
    rows: list[AccountingCompareRowDTO] = []
    missing: list[AccountingMissingRowDTO] = []
    top_gaps: list[AccountingCompareRowDTO] = []

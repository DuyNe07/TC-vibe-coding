"""DTOs of UC-55..UC-64 (đợt 2, bổ sung 2026-11-10): giá nguyên liệu, hàng sắp về, giá báo khách, so giá xuất kho."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, UploadedFileDTO
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO
from backend.features.yarn_costing.models.enums import (
    CottonOrigin,
    FactoryCode,
    Incoterm,
    MaterialDecision,
    MaterialMarket,
    PriceCurrency,
    PriceGroupKind,
    PriceKind,
    StockSection,
)

ZERO = Decimal(0)


class MaterialSaveResponse(BaseResponseDTO):
    message: str
    saved_count: int = 0


# ---- UC-55 / UC-57 ----
class PriceGroupDTO(BaseDTO):
    id: str
    name: str
    kind: PriceGroupKind | None = None  # None = Cotton (phương án)
    origin: CottonOrigin | None = None
    note: str = ""
    code_count: int = 0


class StockItemDTO(BaseDTO):
    accounting_code: str
    item_name: str = ""
    ica_name: str = ""
    decision: MaterialDecision
    price_group_id: str | None = None
    market: MaterialMarket
    closing_qty: Decimal | None = None
    updated_by: str = ""


class GetMaterialSetupRequest(BaseRequestDTO):
    pass


class MaterialSetupResponse(BaseResponseDTO):
    groups: list[PriceGroupDTO] = []  # 4.22 only
    group_options: list[PriceGroupDTO] = []  # Cotton (phương án) + 4.22
    stock_items: list[StockItemDTO] = []
    undeclared_count: int = 0
    latest_period: str = ""


class SavePriceGroupRequest(BaseRequestDTO):
    group_id: str | None = None
    name: str = ""
    kind: PriceGroupKind = PriceGroupKind.XO
    origin: CottonOrigin | None = None
    note: str = ""
    delete: bool = False


class StockItemRowDTO(BaseDTO):
    accounting_code: str
    decision: MaterialDecision
    price_group_id: str | None = None
    market: MaterialMarket


class SaveStockItemSettingsRequest(BaseRequestDTO):
    rows: list[StockItemRowDTO] = []


# ---- UC-56 ----
class ImportStockFileRequest(BaseRequestDTO):
    file: UploadedFileDTO
    period: str = ""  # yyyy-mm chosen on screen; empty = read from the file
    commit: bool = False


class StockImportResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    period: str = ""
    period_read: str = ""
    material_count: int = 0
    yarn_count: int = 0
    accessory_count: int = 0
    new_codes: int = 0
    replace_note: str = ""
    rejected_rows: list[RejectedRowDTO] = []


class ListStockMonthsRequest(BaseRequestDTO):
    pass


class StockMonthDTO(BaseDTO):
    id: str
    period: str
    file_name: str = ""
    material_count: int = 0
    yarn_count: int = 0
    accessory_count: int = 0
    imported_by: str = ""
    imported_at: datetime | None = None


class StockMonthListResponse(BaseResponseDTO):
    items: list[StockMonthDTO] = []


# ---- UC-58 ----
class CottonShareDTO(BaseDTO):
    origin: CottonOrigin
    percent: Decimal  # fraction


class RecoveryDTO(BaseDTO):
    group_id: str
    group_name: str = ""
    usd_per_kg: Decimal = ZERO


class GetMonthlySettingRequest(BaseRequestDTO):
    period: str


class MonthlySettingResponse(BaseResponseDTO):
    period: str
    saved: bool = False
    copied_from: str = ""
    norm_factor: Decimal
    default_fi: Decimal
    cotton_plan_note: str = ""
    cotton_plan: list[CottonShareDTO] = []
    recoveries: list[RecoveryDTO] = []
    group_options: list[PriceGroupDTO] = []
    updated_by: str = ""


class SaveMonthlySettingRequest(BaseRequestDTO):
    period: str
    norm_factor: Decimal
    default_fi: Decimal
    cotton_plan_note: str = ""
    cotton_plan: list[CottonShareDTO] = []
    recoveries: list[RecoveryDTO] = []


# ---- UC-59 ----
class AverageSourceDTO(BaseDTO):
    kind: str
    code: str = ""
    name: str = ""
    market: MaterialMarket
    quantity: Decimal
    unit_usd: Decimal


class AverageRowDTO(BaseDTO):
    group_id: str
    group_name: str
    market: MaterialMarket
    stock_qty: Decimal = ZERO
    stock_unit: Decimal | None = None
    arrival_qty: Decimal = ZERO
    arrival_unit: Decimal | None = None
    total_qty: Decimal = ZERO
    average: Decimal | None = None
    recovery: Decimal = ZERO
    net_usd: Decimal | None = None
    net_vnd: Decimal | None = None
    note: str = ""
    sources: list[AverageSourceDTO] = []


class GetMaterialAveragesRequest(BaseRequestDTO):
    period: str


class MaterialAveragesResponse(BaseResponseDTO):
    period: str
    stock_period: str = ""
    exchange_rate: Decimal | None = None
    plan_text: str = ""
    problem: str = ""  # BR-89 / no stock file: nothing computed
    undeclared_codes: int = 0
    undeclared_lots: int = 0
    rows: list[AverageRowDTO] = []


# ---- UC-60 / UC-61 ----
class ImportArrivalFileRequest(BaseRequestDTO):
    file: UploadedFileDTO
    commit: bool = False


class ArrivalImportResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    sheet: str = ""
    valid_count: int = 0
    s1_count: int = 0
    s4_count: int = 0
    replace_count: int = 0
    new_pairs: int = 0
    rejected_rows: list[RejectedRowDTO] = []


class ArrivalLotDTO(BaseDTO):
    id: str
    supplier: str
    commodity: str = ""
    description: str
    spec: str = ""
    contract_no: str = ""
    contract_date: date | None = None
    quantity: Decimal
    unit_price: Decimal
    price_currency: PriceCurrency
    receiving_price: Decimal | None = None
    term: str = ""
    origin_country: str = ""
    eta_warehouse: date
    warehouse: str = ""
    factory_code: FactoryCode
    market: MaterialMarket
    note: str = ""
    group_name: str = ""
    decision: MaterialDecision = MaterialDecision.CHUA_KHAI_BAO
    from_file: bool = True


class ArrivalMappingDTO(BaseDTO):
    supplier_key: str
    description_key: str
    supplier: str = ""
    description: str = ""
    lot_count: int = 0
    decision: MaterialDecision
    price_group_id: str | None = None


class ArrivalImportDTO(BaseDTO):
    file_name: str = ""
    sheet_name: str = ""
    lot_count: int = 0
    rejected_count: int = 0
    imported_by: str = ""
    imported_at: datetime | None = None


class ListArrivalsRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = FactoryCode.S4
    month: str = ""  # yyyy-mm of the warehouse ETA
    group_id: str = ""
    market: MaterialMarket | None = None
    only_unmapped: bool = False


class ArrivalListResponse(BaseResponseDTO):
    lots: list[ArrivalLotDTO] = []
    mappings: list[ArrivalMappingDTO] = []
    imports: list[ArrivalImportDTO] = []
    months: list[str] = []
    groups: list[PriceGroupDTO] = []
    total_qty: Decimal = ZERO
    unmapped_count: int = 0


class ArrivalLotRowDTO(BaseDTO):
    id: str | None = None
    supplier: str = ""
    commodity: str = ""
    description: str = ""
    spec: str = ""
    contract_no: str = ""
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    receiving_price: Decimal | None = None
    eta_warehouse: date | None = None
    warehouse: str = ""
    factory_code: FactoryCode | None = None
    market: MaterialMarket | None = None
    note: str = ""


class SaveArrivalLotsRequest(BaseRequestDTO):
    rows: list[ArrivalLotRowDTO] = []
    deleted_ids: list[str] = []


class ArrivalMappingRowDTO(BaseDTO):
    supplier_key: str
    description_key: str
    decision: MaterialDecision
    price_group_id: str | None = None


class SaveArrivalMappingsRequest(BaseRequestDTO):
    rows: list[ArrivalMappingRowDTO] = []


# ---- UC-62 / UC-63 ----
class AccountingSuggestionDTO(BaseDTO):
    code: str
    name: str = ""
    stock_qty: Decimal = ZERO


class QuoteFormComponentDTO(BaseDTO):
    material_label: str
    ratio: Decimal
    loss: Decimal
    suggested_group_id: str = ""


class GetQuoteFormRequest(BaseRequestDTO):
    line_code: str
    period: str


class QuoteFormResponse(BaseResponseDTO):
    line_code: str = ""
    yarn_name: str = ""
    components: list[QuoteFormComponentDTO] = []
    accounting_suggestions: list[AccountingSuggestionDTO] = []
    default_accounting_code: str = ""
    norm_factor: Decimal = Decimal("1.10")
    default_fi: Decimal = Decimal("0.03")
    group_options: list[PriceGroupDTO] = []
    has_trial_line: bool = False


class QuoteComponentDTO(BaseDTO):
    material_label: str
    ratio: Decimal
    loss: Decimal = ZERO
    price_group_id: str = ""
    price_group: str = ""
    average_usd: Decimal = ZERO
    recovery_usd: Decimal = ZERO
    net_usd: Decimal = ZERO
    cost_usd: Decimal = ZERO


class QuoteDTO(BaseDTO):
    id: str = ""
    quote_no: str = ""
    period: str
    line_code: str
    price_kind: PriceKind
    yarn_name: str = ""
    accounting_code: str = ""
    customer_name: str = ""
    market: MaterialMarket
    order_qty: Decimal
    norm_factor: Decimal
    gp_percent: Decimal
    commission_percent: Decimal
    incoterm: Incoterm
    fi_usd: Decimal = ZERO
    exchange_rate: Decimal
    norm_vnd: Decimal = ZERO
    material_usd: Decimal = ZERO
    norm_usd: Decimal = ZERO
    new_cost_usd: Decimal = ZERO
    stock_qty: Decimal = ZERO
    stock_cost_usd: Decimal | None = None
    avg_cost_usd: Decimal = ZERO
    fob_usd: Decimal = ZERO
    cif_usd: Decimal | None = None
    components: list[QuoteComponentDTO] = []
    note: str = ""
    created_by: str = ""
    created_at: datetime | None = None


class CalculateQuoteRequest(BaseRequestDTO):
    period: str
    line_code: str = ""
    price_kind: PriceKind = PriceKind.THUONG
    accounting_code: str = ""
    customer_name: str = ""
    market: MaterialMarket = MaterialMarket.NOI_DIA
    order_qty: Decimal = ZERO
    norm_factor: Decimal = Decimal("1.10")
    gp_percent: Decimal = ZERO  # fractions
    commission_percent: Decimal = ZERO
    incoterm: Incoterm = Incoterm.FOB
    fi_usd: Decimal = ZERO
    groups: dict[str, str] = {}  # material label → price group id
    note: str = ""
    commit: bool = False


class QuoteResponse(BaseResponseDTO):
    message: str = ""
    saved: bool = False
    quote: QuoteDTO


class ListQuotesRequest(BaseRequestDTO):
    date_from: date | None = None
    date_to: date | None = None
    period: str = ""
    customer: str = ""
    search: str = ""


class QuoteListResponse(BaseResponseDTO):
    items: list[QuoteDTO] = []
    customers: list[str] = []
    periods: list[str] = []


class ExportQuotesRequest(ListQuotesRequest):
    pass


class DeleteQuoteRequest(BaseRequestDTO):
    quote_id: str


# ---- UC-64 ----
class GetStockOutComparisonRequest(BaseRequestDTO):
    period: str = ""  # empty = latest stock month
    gap_percent: Decimal = Decimal(10)
    only_gap: bool = False


class StockOutRowDTO(BaseDTO):
    section: StockSection
    accounting_code: str
    item_name: str = ""
    group_name: str = ""
    market: MaterialMarket | None = None
    out_qty: Decimal
    out_unit_usd: Decimal
    out_unit_vnd: Decimal
    compare_usd: Decimal | None = None
    quote_no: str = ""
    quote_date: date | None = None
    difference: Decimal | None = None
    difference_percent: Decimal | None = None
    note: str = ""
    is_gap: bool = False


class StockOutComparisonResponse(BaseResponseDTO):
    period: str = ""
    months: list[str] = []
    problem: str = ""
    exchange_rate: Decimal | None = None
    material_rows: list[StockOutRowDTO] = []
    yarn_rows: list[StockOutRowDTO] = []
    material_count: int = 0
    yarn_count: int = 0
    gap_count: int = 0
    no_compare_count: int = 0

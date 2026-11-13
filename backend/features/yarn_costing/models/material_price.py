"""Đợt 2 (bổ sung 2026-11-10): 4.22 nhóm giá nguyên liệu, 4.23 khai báo mã kho, 4.24 tháng kho, 4.25 khai báo tháng,
4.26 lô hàng sắp về, 4.27 ghép hàng sắp về với nhóm giá, 4.28 lần tính giá báo khách."""

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
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
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate

ZERO = Decimal(0)
COTTON_PLAN_ID = "cotton-plan"  # fixed group "Cotton (phương án)" (BR-92), never stored in 4.22
COTTON_PLAN_NAME = "Cotton (phương án)"


class MaterialPriceGroup(BaseEntity):
    """4.22 Nhóm giá nguyên liệu."""

    name: str = Field(min_length=1, max_length=100)
    kind: PriceGroupKind
    origin: CottonOrigin | None = None
    note: str = ""
    created_by: str = ""
    updated_by: str = ""


class StockItemSetting(BaseEntity):
    """4.23 Khai báo mã kho nguyên liệu (one row per accounting code ever seen in the Nguyên liệu part)."""

    accounting_code: str
    item_name: str = ""
    ica_name: str = ""
    decision: MaterialDecision = MaterialDecision.CHUA_KHAI_BAO
    price_group_id: str | None = None
    market: MaterialMarket = MaterialMarket.CHUNG
    updated_by: str = ""


class StockMonth(BaseEntity):
    """4.24 Tháng kho (one version in use per period - BR-87)."""

    period: str  # yyyy-mm
    factory_code: FactoryCode = FactoryCode.S4
    file_name: str = ""
    material_count: int = 0
    yarn_count: int = 0
    accessory_count: int = 0
    imported_by: str = ""


class StockLine(BaseEntity):
    """4.24.1 Dòng kho (VND values as in the accounting report)."""

    month_id: str
    period: str
    section: StockSection
    ica_name: str = ""
    accounting_code: str
    item_name: str = ""
    unit: str = ""
    opening_qty: Decimal = ZERO
    opening_value: Decimal = ZERO
    in_qty: Decimal = ZERO
    in_value: Decimal = ZERO
    out_qty: Decimal = ZERO
    out_value: Decimal = ZERO
    closing_qty: Decimal = ZERO
    closing_value: Decimal = ZERO


class CottonShare(BaseValueObject):
    origin: CottonOrigin
    percent: Decimal  # fraction: 0.31 = 31%


class GroupRecovery(BaseValueObject):
    group_id: str  # 4.22 id or COTTON_PLAN_ID
    usd_per_kg: Decimal = ZERO


class MonthlyMaterialSetting(BaseEntity):
    """4.25 Khai báo tháng."""

    period: str
    norm_factor: Decimal = Decimal("1.10")
    default_fi: Decimal = Decimal("0.03")
    cotton_plan_note: str = ""
    cotton_plan: list[CottonShare] = Field(default_factory=list)
    recoveries: list[GroupRecovery] = Field(default_factory=list)
    copied_from: str = ""
    updated_by: str = ""
    # BR-113 (bổ sung 2026-11-13): bông Supima pha trong phương án bông
    supima_group_id: str = ""
    coin_usd: Decimal = Decimal("0.552")
    coin_tax: Decimal = Decimal("0.05")

    def recovery_of(self, group_id: str) -> Decimal:
        return next((r.usd_per_kg for r in self.recoveries if r.group_id == group_id), ZERO)


class ArrivalImport(BaseEntity):
    """4.26.1 Lần nhập file hàng sắp về."""

    file_name: str = ""
    sheet_name: str = ""
    lot_count: int = 0
    rejected_count: int = 0
    imported_by: str = ""


class ArrivalLot(BaseEntity):
    """4.26 Lô nguyên liệu sắp về."""

    import_id: str | None = None
    supplier: str = Field(min_length=1, max_length=200)
    commodity: str = ""
    description: str = Field(min_length=1, max_length=300)
    spec: str = ""
    contract_no: str = ""
    contract_date: date | None = None
    quantity: Decimal
    unit_price: Decimal
    price_currency: PriceCurrency = PriceCurrency.USD
    receiving_price: Decimal | None = None
    term: str = ""
    origin_country: str = ""
    shipment_date: date | None = None
    eta_port: date | None = None
    eta_warehouse: date
    warehouse: str = ""
    factory_code: FactoryCode = FactoryCode.S4
    market: MaterialMarket = MaterialMarket.CHUNG
    note: str = ""
    created_by: str = ""
    updated_by: str = ""


class ArrivalMapping(BaseEntity):
    """4.27 Ghép (nhà cung cấp, mô tả) → nhóm giá."""

    supplier_key: str
    description_key: str
    supplier: str = ""  # as last seen, for display
    description: str = ""
    decision: MaterialDecision = MaterialDecision.CHUA_KHAI_BAO
    price_group_id: str | None = None
    updated_by: str = ""


class QuoteComponent(BaseValueObject):
    """4.28.1 Thành phần của lần tính."""

    material_label: str
    ratio: Decimal
    loss: Decimal = ZERO
    price_group_id: str = ""
    price_group: str = ""
    average_usd: Decimal = ZERO
    recovery_usd: Decimal = ZERO
    net_usd: Decimal = ZERO
    cost_usd: Decimal = ZERO
    # BR-111 (bổ sung 2026-11-13): phần pha Supima của thành phần bông
    supima_ratio: Decimal = ZERO
    normal_net: Decimal = ZERO
    normal_loss: Decimal = ZERO
    supima_net: Decimal = ZERO
    supima_loss: Decimal = ZERO


class Quote(BaseEntity):
    """4.28 Lần tính giá báo khách (numbers frozen when saved - BR-97)."""

    quote_no: str
    period: str
    line_code: str
    base_code: str = ""
    price_kind: PriceKind = PriceKind.THUONG
    yarn_name: str = ""
    accounting_code: str = ""
    customer_name: str = ""
    market: MaterialMarket = MaterialMarket.NOI_DIA
    order_qty: Decimal
    norm_factor: Decimal
    gp_percent: Decimal = ZERO  # fractions
    commission_percent: Decimal = ZERO
    incoterm: Incoterm = Incoterm.FOB
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
    components: list[QuoteComponent] = Field(default_factory=list)
    note: str = ""
    created_by: str = ""
    created_username: str = ""
    # BR-110 / BR-111 (bổ sung 2026-11-13)
    cotton_plan: list[CottonShare] = Field(default_factory=list)
    supima_percent: Decimal = ZERO
    supima_coin: bool = False
    coin_fee_usd: Decimal = ZERO


# ---- values computed on the fly (not stored) ----
class AverageSource(BaseValueObject):
    """One stock code or arrival lot counted in an average (UC-59 chi tiết)."""

    kind: str  # "Tồn" / "Hàng về"
    code: str = ""
    name: str = ""
    market: MaterialMarket = MaterialMarket.CHUNG
    quantity: Decimal = ZERO
    unit_usd: Decimal = ZERO


class GroupAverage(BaseValueObject):
    """BR-92: average price of one group + market for month M."""

    group_id: str
    group_name: str
    market: MaterialMarket
    stock_qty: Decimal = ZERO
    stock_value: Decimal = ZERO  # USD
    arrival_qty: Decimal = ZERO
    arrival_value: Decimal = ZERO  # USD
    average: Decimal | None = None
    recovery: Decimal = ZERO
    net: Decimal | None = None
    note: str = ""
    sources: list[AverageSource] = Field(default_factory=list)

    @property
    def total_qty(self) -> Decimal:
        return self.stock_qty + self.arrival_qty


class ParsedRows(BaseValueObject):
    """Rows of an uploaded file keyed by field name (excel row, cells) + the problem that stops reading, if any."""

    sheet: str = ""
    rows: list[tuple[int, dict[str, Any]]] = Field(default_factory=list)
    problem: str = ""
    period_text: str = ""  # stock file: first CF_APE_DATE value


class StockOutCompareRow(BaseValueObject):
    """BR-99: one stock code compared (Nguyên liệu with the group average, Sợi thành phẩm with the latest quote)."""

    section: StockSection
    accounting_code: str
    item_name: str = ""
    group_name: str = ""
    market: MaterialMarket | None = None
    out_qty: Decimal = ZERO
    out_unit_usd: Decimal = ZERO
    out_unit_vnd: Decimal = ZERO
    compare_usd: Decimal | None = None
    quote_no: str = ""
    quote_date: date | None = None
    difference: Decimal | None = None
    difference_percent: Decimal | None = None
    note: str = ""
    is_gap: bool = False


class MonthInputs(BaseValueObject):
    """Everything BR-92 reads for month M (loaded once by the repositories, computed by the business)."""

    period: str
    stock_month: StockMonth | None = None  # tháng kho M−1
    stock_lines: list[StockLine] = Field(default_factory=list)
    settings: dict[str, StockItemSetting] = Field(default_factory=dict)
    groups: dict[str, MaterialPriceGroup] = Field(default_factory=dict)
    lots: list[ArrivalLot] = Field(default_factory=list)
    mappings: dict[tuple[str, str], ArrivalMapping] = Field(default_factory=dict)
    monthly: list[MonthlyMaterialSetting] = Field(default_factory=list)
    rates: list[ExchangeRate] = Field(default_factory=list)


class SupimaMix(BaseValueObject):
    """BR-111: what the cotton component of one quote mixes in (s = 0 → nothing)."""

    ratio: Decimal = ZERO  # s, fraction of the cotton part
    net: Decimal = ZERO  # Giá tính Supima (BQ − hồi phế)
    coin_fee: Decimal = ZERO
    loss: Decimal = ZERO  # tổng tiêu hao nhóm "CM (SUPIMA 100%)"
    normal_loss: Decimal = ZERO  # tổng tiêu hao nhóm "CM" / "CM COMPACT"

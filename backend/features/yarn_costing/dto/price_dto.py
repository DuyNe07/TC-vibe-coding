"""DTOs of UC-25..UC-29 (dòng CK/PP, bảng giá, mã kế toán, xuất Excel)."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.common_dto import ActorDTO
from backend.features.yarn_costing.dto.pricing_dto import PriceLineDTO
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, Technology, YarnStatus


class CreateAdjustmentLineRequest(BaseRequestDTO):
    actor: ActorDTO
    yarn_code: str
    line_type: LineType
    percent: Decimal
    reason: str = ""
    order_ref: str = ""


class PriceLineResponse(BaseResponseDTO):
    message: str
    line: PriceLineDTO


class DeleteAdjustmentLineRequest(BaseRequestDTO):
    actor: ActorDTO
    line_code: str


class ListPriceLinesRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None
    line_types: list[LineType] | None = None
    statuses: list[YarnStatus] | None = None
    technology: Technology | None = None
    yarn_group: str | None = None
    has_accounting_code: bool | None = None
    priced_from: date | None = None
    priced_to: date | None = None
    keyword: str = ""


class ExportPriceLinesRequest(ListPriceLinesRequest):
    """UC-29: same filters as the screen."""


class PriceLineRowDTO(BaseDTO):
    """One row of sheet 'Bang gia' (5.4)."""

    stt: int
    factory_code: FactoryCode
    line_code: str
    line_type: LineType
    base_code: str
    yarn_code: str
    yarn_name: str
    yarn_group: str = ""
    count: Decimal | None = None
    technology: Technology
    loss_group_key: str = ""
    components_text: str = ""
    labor: Decimal
    depreciation: Decimal
    electricity: Decimal
    materials: Decimal
    overhead: Decimal
    total_vnd: Decimal
    usd_per_kg: Decimal | None = None
    exchange_rate: Decimal | None = None
    packaging_code: str | None = None
    packaging_name: str = ""
    first_priced_at: date | None = None
    effective_date: date | None = None
    status: YarnStatus
    accounting_code: str | None = None
    adjustment_percent: Decimal | None = None
    adjustment_reason: str = ""
    order_ref: str = ""
    is_locked: bool = False


class PriceLineListResponse(BaseResponseDTO):
    items: list[PriceLineRowDTO] = []
    total_count: int = 0
    with_accounting_code_count: int = 0
    not_priced_count: int = 0
    waiting_count: int = 0
    exchange_rate: Decimal | None = None
    exchange_rate_date: date | None = None
    trial_factor: Decimal


class SetAccountingCodeRequest(BaseRequestDTO):
    actor: ActorDTO
    line_code: str
    accounting_code: str = ""

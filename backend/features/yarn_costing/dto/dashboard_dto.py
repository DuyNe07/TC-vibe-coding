"""DTOs of UC-30..UC-32 (giá bất thường, NSM bất thường, dashboard)."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.common_dto import RecalcBatchDTO
from backend.features.yarn_costing.models.enums import FactoryCode


class CheckPriceAnomaliesRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None


class PriceAnomalyDTO(BaseDTO):
    factory_code: str
    technology: str
    yarn_group: str
    loss_group_key: str
    prev_code: str
    prev_count: Decimal | None = None
    prev_total: Decimal
    next_code: str
    next_count: Decimal | None = None
    next_total: Decimal
    reason: str


class PriceAnomalyResponse(BaseResponseDTO):
    items: list[PriceAnomalyDTO] = []
    group_count: int = 0
    pair_count: int = 0


class CheckNsmAnomaliesRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None


class NsmAnomalyDTO(BaseDTO):
    factory_code: str
    technology: str
    loss_group_key: str
    stage_code: str
    common_value: Decimal
    yarn_code: str
    nsm: Decimal
    reason: str = ""


class NsmAnomalyResponse(BaseResponseDTO):
    items: list[NsmAnomalyDTO] = []


class GetDashboardRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None
    date_from: date
    date_to: date


class WeeklyStatDTO(BaseDTO):
    week_start: date
    new_requests: int = 0
    fulfilment_ratio: Decimal | None = None


class DashboardResponse(BaseResponseDTO):
    quoted_count: int = 0
    ordered_count: int = 0
    ordered_ratio: Decimal | None = None
    new_request_count: int = 0
    fulfilment_ratio: Decimal | None = None
    waiting_count: int = 0
    weekly: list[WeeklyStatDTO] = []
    status_counts: dict[str, int] = {}
    last_batch: RecalcBatchDTO | None = None
    last_batch_up: int = 0
    last_batch_down: int = 0
    last_batch_avg_percent: Decimal | None = None
    has_data: bool = False
    empty_message: str = ""

"""DTOs of UC-38 (dữ liệu tham chiếu cho mọi màn hình)."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.master_dto import (
    PackagingRowDTO,
    ProcessRouteRowDTO,
    RateLineRowDTO,
    RecoveryRowDTO,
    StageRowDTO,
)
from backend.features.yarn_costing.models.enums import FactoryCode


class FactoryDTO(BaseDTO):
    code: FactoryCode
    name: str
    carding_stages: list[str] = []
    code_prefix: str
    default_packaging_code: str | None = None


class RateVersionDTO(BaseDTO):
    version_code: str
    factory_code: FactoryCode
    effective_date: date
    reason: str
    created_by: str = ""
    created_at: datetime
    lines: list[RateLineRowDTO] = []


class ExchangeRateDTO(BaseDTO):
    effective_date: date
    rate: Decimal
    note: str = ""
    created_by: str = ""
    created_at: datetime


class GetReferenceDataRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None


class ReferenceDataResponse(BaseResponseDTO):
    factories: list[FactoryDTO] = []
    stages: list[StageRowDTO] = []
    current_rate: RateVersionDTO | None = None
    rate_versions: list[RateVersionDTO] = []
    packaging: list[PackagingRowDTO] = []
    recovery: list[RecoveryRowDTO] = []
    routes: list[ProcessRouteRowDTO] = []
    exchange_rates: list[ExchangeRateDTO] = []
    current_exchange_rate: ExchangeRateDTO | None = None
    trial_factor: Decimal
    yarn_groups: list[str] = []
    data_warnings: list[str] = []

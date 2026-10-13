"""DTOs of UC-03..UC-09 (dữ liệu nền), UC-36 / UC-37 (lần tính lại)."""

from datetime import date
from decimal import Decimal

from pydantic import field_validator

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, FileDownloadDTO
from backend.features.yarn_costing.dto.common_dto import RecalcBatchDTO
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    LineType,
    RateCodeSource,
    RecoveryType,
    SecondaryMethod,
    Technology,
)


class StageRowDTO(BaseDTO):
    factory_code: FactoryCode | None = None
    stage_code: str = ""
    stage_name: str = ""
    stage_group: str = ""
    sequence: int | None = None
    is_packaging: bool = False
    recovery_type: RecoveryType = RecoveryType.KHONG
    blend_slot: str = "Không"
    is_carding: bool = False
    max_passes: int | None = None
    is_merge_stage: bool = False
    secondary_method: SecondaryMethod = SecondaryMethod.BINH_QUAN
    cumulative_stages: list[str] = []
    varies_with_count: bool = False
    rate_code_source: RateCodeSource = RateCodeSource.CHINH_CONG_DOAN

    @field_validator("cumulative_stages", mode="before")
    @classmethod
    def _split_text(cls, value: object) -> object:
        """An Excel-like cell may send 'CM, DCM, MD1' as one text."""
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value if value is not None else []


class SaveStageConfigRequest(BaseRequestDTO):
    factory_code: FactoryCode
    rows: list[StageRowDTO]
    effective_date: date | None = None
    reason: str = ""


class RateLineRowDTO(BaseDTO):
    factory_code: FactoryCode | None = None
    rate_code: str = ""
    labor: Decimal | None = None
    depreciation: Decimal | None = None
    electricity: Decimal | None = None
    materials: Decimal | None = None
    overhead: Decimal | None = None
    note: str = ""
    total_rate: Decimal | None = None


class ApplyRateVersionRequest(BaseRequestDTO):
    factory_code: FactoryCode
    rows: list[RateLineRowDTO]
    effective_date: date | None = None
    reason: str = ""


class PackagingRowDTO(BaseDTO):
    factory_code: FactoryCode | None = None
    code: str = ""
    name: str = ""
    weight_kg: Decimal | None = None
    man_days: Decimal | None = None
    minutes_per_kg: Decimal | None = None
    active: bool = True
    is_default: bool = False
    has_rate: bool = False
    selectable: bool = False


class SavePackagingTypesRequest(BaseRequestDTO):
    factory_code: FactoryCode
    rows: list[PackagingRowDTO]
    effective_date: date | None = None
    reason: str = ""
    preview: bool = False


class RecoveryRowDTO(BaseDTO):
    factory_code: FactoryCode | None = None
    recovery_type: RecoveryType
    rate: Decimal | None = None


class SaveRecoveryRatesRequest(BaseRequestDTO):
    factory_code: FactoryCode
    rows: list[RecoveryRowDTO]
    effective_date: date | None = None
    reason: str = ""


class RecalculateNotPricedRequest(BaseRequestDTO):
    """UC-43: tính lại các mã 'Chưa tính được' của một xưởng (BR-65)."""

    factory_code: FactoryCode
    effective_date: date | None = None
    reason: str = ""


class ProcessRouteRowDTO(BaseDTO):
    factory_code: FactoryCode | None = None
    yarn_group: str = ""
    technology: Technology | None = None
    component_count: int | None = None
    route_text: str = ""
    route_stages: list[str] = []


class SaveProcessRoutesRequest(BaseRequestDTO):
    factory_code: FactoryCode
    rows: list[ProcessRouteRowDTO]


class AddExchangeRateRequest(BaseRequestDTO):
    effective_date: date
    rate: Decimal | None = None
    note: str = ""


class UpdateTrialFactorRequest(BaseRequestDTO):
    trial_factor: Decimal | None = None
    effective_date: date | None = None
    reason: str = ""


class ListRecalcBatchesRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None


class RecalcBatchListResponse(BaseResponseDTO):
    items: list[RecalcBatchDTO] = []


class GetRecalcDiffRequest(BaseRequestDTO):
    batch_id: str
    line_types: list[LineType] | None = None


class RecalcDiffRowDTO(BaseDTO):
    line_code: str
    yarn_name: str = ""
    line_type: LineType
    old_total: Decimal
    new_total: Decimal
    diff_vnd: Decimal
    diff_percent: Decimal | None = None


class RecalcDiffResponse(BaseResponseDTO):
    batch: RecalcBatchDTO
    items: list[RecalcDiffRowDTO] = []
    up_count: int = 0
    down_count: int = 0
    unchanged_count: int = 0
    avg_percent: Decimal | None = None
    file: FileDownloadDTO

"""DTOs of UC-20..UC-24 (NSM, tính giá, chi tiết, ĐCNSM)."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.common_dto import YarnComponentDTO

__all__ = [
    "CorrectYarnNsmRequest",
    "CreateNsmRevisionRequest",
    "GetYarnDetailRequest",
    "NsmSuggestionResponse",
    "PriceHistoryDTO",
    "PriceLineDTO",
    "PricingResultResponse",
    "SaveYarnNsmRequest",
    "StageCostDTO",
    "StageInputDTO",
    "SuggestNsmRequest",
    "YarnComponentDTO",
    "YarnDetailResponse",
]
from backend.features.yarn_costing.dto.request_dto import YarnDTO, YarnSummaryDTO
from backend.features.yarn_costing.models.enums import LineType, NsmMode, PriceEvent


class StageCostDTO(BaseDTO):
    sequence: int
    stage_code: str
    stage_name: str
    material_label: str = ""
    pass_no: int | None = None
    nsm: Decimal | None = None
    run_minutes: Decimal
    loss: Decimal
    loss_note: str = ""  # BR-64
    cumulative_loss: Decimal
    total_rate: Decimal
    cost_per_kg: Decimal
    labor: Decimal
    depreciation: Decimal
    electricity: Decimal
    materials: Decimal
    overhead: Decimal


class PriceLineDTO(BaseDTO):
    yarn_code: str
    line_code: str
    line_type: LineType
    adjustment_percent: Decimal | None = None
    adjustment_reason: str = ""
    order_ref: str = ""
    labor: Decimal
    depreciation: Decimal
    electricity: Decimal
    materials: Decimal
    overhead: Decimal
    total_vnd: Decimal
    usd_per_kg: Decimal | None = None
    accounting_code: str | None = None
    accounting_code_by: str = ""
    accounting_code_at: datetime | None = None
    created_by: str = ""
    created_at: datetime


class PriceHistoryDTO(BaseDTO):
    line_code: str
    changed_at: datetime
    changed_by: str = ""
    event: PriceEvent
    batch_id: str | None = None
    effective_date: date | None = None
    old_labor: Decimal | None = None
    old_depreciation: Decimal | None = None
    old_electricity: Decimal | None = None
    old_materials: Decimal | None = None
    old_overhead: Decimal | None = None
    old_total: Decimal | None = None
    new_labor: Decimal
    new_depreciation: Decimal
    new_electricity: Decimal
    new_materials: Decimal
    new_overhead: Decimal
    new_total: Decimal
    reason: str = ""


class StageInputDTO(BaseDTO):
    stage_code: str
    stage_name: str
    nsm: Decimal | None = None
    reference_nsm: Decimal | None = None


class SuggestNsmRequest(BaseRequestDTO):
    yarn_code: str


class NsmSuggestionResponse(BaseResponseDTO):
    found: bool
    message: str = ""
    reference_yarn_code: str | None = None
    reference_yarn_name: str | None = None
    reference_count: Decimal | None = None
    nsm: dict[str, Decimal] = {}
    components: list[YarnComponentDTO] = []


class SaveYarnNsmRequest(BaseRequestDTO):
    yarn_code: str
    components: list[YarnComponentDTO] = []
    nsm: dict[str, Decimal] = {}  # stages that are not carding lines only
    nsm_mode: NsmMode = NsmMode.TU_NHAP
    reference_yarn_code: str | None = None
    nsm_warning_reason: str = ""
    save: bool = False


class CorrectYarnNsmRequest(SaveYarnNsmRequest):
    """UC-23: same fields as UC-21, on a yarn that already has a price."""


class CreateNsmRevisionRequest(BaseRequestDTO):
    source_yarn_code: str
    adjust_reason: str = ""
    components: list[YarnComponentDTO] = []
    nsm: dict[str, Decimal] = {}
    nsm_warning_reason: str = ""
    save: bool = False


class PricingResultResponse(BaseResponseDTO):
    message: str
    saved: bool = False
    check_passed: bool = False
    reasons: list[str] = []
    warning_stages: list[str] = []
    reference_yarn_code: str | None = None
    components: list[YarnComponentDTO] = []
    stage_details: list[StageCostDTO] = []
    line: PriceLineDTO | None = None
    trial_line: PriceLineDTO | None = None
    yarn: YarnDTO


class GetYarnDetailRequest(BaseRequestDTO):
    yarn_code: str | None = None
    line_code: str | None = None


class YarnDetailResponse(BaseResponseDTO):
    yarn: YarnDTO
    stages: list[StageInputDTO] = []
    stage_details: list[StageCostDTO] = []
    lines: list[PriceLineDTO] = []
    revisions: list[YarnSummaryDTO] = []
    history: list[PriceHistoryDTO] = []
    carding_stages: list[str] = []
    components: list[YarnComponentDTO] = []
    material_options: list[str] = []
    reference_yarn_code: str | None = None

"""DTOs of UC-15..UC-19 and UC-40 (yêu cầu tính giá, danh sách mã, nhận diện tên sợi)."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.yarn_costing.dto.common_dto import ActorDTO, YarnComponentDTO
from backend.features.yarn_costing.models.enums import FactoryCode, NsmMode, Technology, YarnOrigin, YarnStatus


class YarnDTO(BaseDTO):
    """Every field of 4.12 + is_locked."""

    id: str
    factory_code: FactoryCode
    yarn_code: str
    base_code: str
    revision_no: int = 0
    yarn_name: str
    yarn_group: str = ""
    count: Decimal | None = None
    loss_group_key: str = ""
    technology: Technology
    is_compact: bool = False
    packaging_code: str | None = None
    packaging_name: str = ""
    components: list[YarnComponentDTO] = []
    nsm: dict[str, Decimal] = {}
    nsm_mode: NsmMode | None = None
    reference_yarn_code: str | None = None
    nsm_warning_reason: str = ""
    adjust_reason: str = ""
    status: YarnStatus
    status_reasons: list[str] = []
    reject_reason: str = ""
    origin: YarnOrigin
    requested_by: str = ""
    requested_at: datetime
    handled_by: str = ""
    handled_at: datetime | None = None
    first_priced_at: date | None = None
    last_calculated_at: datetime | None = None
    effective_date: date | None = None
    is_locked: bool = False
    total_vnd: Decimal | None = None
    usd_per_kg: Decimal | None = None


class YarnSummaryDTO(BaseDTO):
    yarn_code: str
    factory_code: FactoryCode
    base_code: str
    revision_no: int = 0
    yarn_name: str
    packaging_code: str | None = None
    status: YarnStatus
    origin: YarnOrigin
    requested_by: str = ""
    requested_at: datetime
    handled_by: str = ""
    handled_at: datetime | None = None
    reason: str = ""
    total_vnd: Decimal | None = None
    usd_per_kg: Decimal | None = None
    is_locked: bool = False
    first_priced_at: date | None = None
    loss_group_key: str = ""


class CreateYarnRequestRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    yarn_name: str
    packaging_code: str = ""


class UpdateYarnRequestRequest(BaseRequestDTO):
    actor: ActorDTO
    yarn_code: str
    yarn_name: str
    packaging_code: str = ""


class CancelYarnRequestRequest(BaseRequestDTO):
    actor: ActorDTO
    yarn_code: str


class RejectYarnRequestRequest(BaseRequestDTO):
    actor: ActorDTO
    yarn_code: str
    reason: str = ""


class YarnResponse(BaseResponseDTO):
    message: str
    yarn: YarnDTO


class ListYarnsRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None
    statuses: list[YarnStatus] | None = None
    date_from: date | None = None
    date_to: date | None = None
    keyword: str = ""
    origin: str | None = None
    oldest_first: bool = False


class YarnListResponse(BaseResponseDTO):
    items: list[YarnSummaryDTO] = []
    status_counts: dict[str, int] = {}


class AnalyzeYarnNameRequest(BaseRequestDTO):
    factory_code: FactoryCode
    yarn_name: str = ""


class YarnNameAnalysisResponse(BaseResponseDTO):
    valid: bool
    message: str = ""
    yarn_group: str = ""
    count: Decimal | None = None
    technology: Technology | None = None
    is_compact: bool = False
    loss_group_key: str = ""
    loss_group_exists: bool = False
    duplicate_code: str | None = None


class CheckRequestSubmitRequest(BaseRequestDTO):
    """UC-42: ``group_code`` = nhóm đã xác nhận trong phiên làm việc (None = chưa xác nhận)."""

    group_code: str | None = None
    factory_code: FactoryCode | None = None


class RequestSubmitCheckResponse(BaseResponseDTO):
    allowed: bool
    reasons: list[str] = []

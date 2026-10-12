"""Shared DTOs (actor of every mutating request, simple responses) and the enums pages need."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseResponseDTO
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    GroupCode,
    ImportMode,
    LineType,
    LossGroupLevel,
    NsmMode,
    PriceEvent,
    RateCodeSource,
    RecoveryType,
    SecondaryMethod,
    Technology,
    YarnOrigin,
    YarnStatus,
)

__all__ = [
    "ActorDTO",
    "FactoryCode",
    "GroupCode",
    "ImportMode",
    "LineType",
    "LossGroupLevel",
    "NsmMode",
    "PriceEvent",
    "RateCodeSource",
    "RecalcBatchDTO",
    "RecalcResultResponse",
    "RecoveryType",
    "SaveCountResponse",
    "SecondaryMethod",
    "Technology",
    "YarnComponentDTO",
    "YarnOrigin",
    "YarnStatus",
]


class ActorDTO(BaseDTO):
    """Nhóm + mã nội bộ + tên người thao tác, gửi kèm mọi lệnh làm thay đổi dữ liệu (BR-46)."""

    group_code: str = ""
    access_code: str = ""
    person_name: str = ""


class YarnComponentDTO(BaseDTO):
    """4.12.1 one row of the component table (Screen 3): material, ratio, carding line ("" = Không chải thô)."""

    material_label: str = ""
    ratio: Decimal | None = None
    carding_stage: str = ""
    pass_no: int | None = None  # output: numbered by the app (BR-56)
    nsm_carding: Decimal | None = None
    reference_nsm: Decimal | None = None  # output: carding NSM of the reference yarn (BR-37)


class SaveCountResponse(BaseResponseDTO):
    message: str
    saved_count: int = 0


class RecalcBatchDTO(BaseDTO):
    batch_id: str
    factory_code: FactoryCode
    trigger: PriceEvent
    effective_date: date
    reason: str = ""
    run_by: str = ""
    run_at: datetime
    yarn_count: int = 0
    changed_line_count: int = 0
    failed_yarn_count: int = 0


class RecalcResultResponse(BaseResponseDTO):
    message: str
    batch: RecalcBatchDTO | None = None
    batches: list[RecalcBatchDTO] = []
    recalculated_count: int = 0
    failed_count: int = 0
    old_value: Decimal | None = None
    will_recalculate: bool = False
    confirm_text: str = ""

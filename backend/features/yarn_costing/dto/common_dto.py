"""Shared DTOs (simple responses), the enums and the role tables pages need."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseResponseDTO
from backend.features.yarn_costing.models.access import (
    INITIAL_IMPORT_USE_CASE,
    ROLE_FACTORY,
    ROLE_LABELS,
    USE_CASE_PERMISSIONS,
)
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
    "INITIAL_IMPORT_USE_CASE",
    "ROLE_FACTORY",
    "ROLE_LABELS",
    "USE_CASE_PERMISSIONS",
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

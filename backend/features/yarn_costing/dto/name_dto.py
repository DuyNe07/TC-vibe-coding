"""DTOs of UC-65..UC-71 (tên sợi, bổ sung 2026-11-11) and of the live name check of Screen 2 (BR-101, BR-102)."""

from datetime import datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, FileDownloadDTO, UploadedFileDTO
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    NameIssueKind,
    NameMode,
    NamePartKind,
    NamePartSource,
    NameWordKind,
    NameWordSource,
    PendingWordStatus,
    YarnStatus,
)


class NameSaveResponse(BaseResponseDTO):
    message: str
    saved_count: int = 0


class UnknownWordDTO(BaseDTO):
    word: str
    suggestion: str = ""


class NamePartDTO(BaseDTO):
    id: str = ""
    kind: NamePartKind
    text: str
    fiber_count: int = 1
    sequence: int = 0
    source: NamePartSource = NamePartSource.PHONG_SO
    reviewed: bool = True


# ---- BR-101 / BR-102: live check (Screen 2, rename block) ----
class CheckYarnNameRequest(BaseRequestDTO):
    mode: NameMode = NameMode.GO_TAY
    yarn_name: str = ""  # Gõ tay
    group: str = ""  # Ghép
    count: Decimal | None = None
    ratios: list[Decimal] = []
    keywords: list[str] = []


class YarnNameCheckResponse(BaseResponseDTO):
    name: str = ""
    problem: str = ""  # builder error or blocking error (parentheses / ratio)
    issues: list[NameIssueKind] = []
    unknown: list[UnknownWordDTO] = []
    suggested_name: str = ""
    groups: list[NamePartDTO] = []
    keywords: list[NamePartDTO] = []


# ---- UC-65 / UC-66 / UC-67 / UC-70: Screen 14 ----
class SuspectNameDTO(BaseDTO):
    factory_code: FactoryCode
    yarn_code: str
    status: YarnStatus
    yarn_name: str
    issues: list[NameIssueKind]
    detail: str = ""
    suggested_name: str = ""


class NameWordDTO(BaseDTO):
    word: str
    kind: NameWordKind
    correct_word: str = ""
    source: NameWordSource = NameWordSource.PHONG_SO


class PendingUseDTO(BaseDTO):
    yarn_code: str
    typed_by: str = ""
    reason: str = ""
    at: datetime | None = None


class PendingWordDTO(BaseDTO):
    id: str
    word: str
    count: int
    status: PendingWordStatus
    last_at: datetime | None = None
    suggestion: str = ""
    resolved_word: str = ""
    uses: list[PendingUseDTO] = []


class GetNameCheckRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None
    issues: list[NameIssueKind] = []  # empty = every kind
    keyword: str = ""


class NameCheckResponse(BaseResponseDTO):
    counts: dict[str, int] = {}
    suspects: list[SuspectNameDTO] = []
    words: list[NameWordDTO] = []
    pending: list[PendingWordDTO] = []
    groups: list[NamePartDTO] = []
    keywords: list[NamePartDTO] = []


class SaveNameDictionaryRequest(BaseRequestDTO):
    words: list[NameWordDTO] = []  # the whole table as edited (missing rows = deleted)


class ResolvePendingWordRequest(BaseRequestDTO):
    pending_id: str
    correct_word: str = ""  # empty = "Thêm vào từ điển"; set = "Sai, sửa thành"
    preview: bool = False


class ResolvePendingResponse(BaseResponseDTO):
    message: str
    yarn_count: int = 0
    group_count: int = 0


class SaveNamePartsRequest(BaseRequestDTO):
    parts: list[NamePartDTO] = []  # both lists as edited (missing rows = deleted)


# ---- UC-68 / UC-69 ----
class RenameYarnRequest(BaseRequestDTO):
    yarn_code: str
    new_name: str
    reason: str = ""
    unknown_word_reason: str = ""
    preview: bool = False


class RenameYarnResponse(BaseResponseDTO):
    message: str = ""
    saved: bool = False
    old_name: str = ""
    new_name: str = ""
    old_loss_group: str = ""
    new_loss_group: str = ""
    unknown: list[UnknownWordDTO] = []


class ExportRenameListRequest(GetNameCheckRequest):
    pass


class ImportRenameFileRequest(BaseRequestDTO):
    file: UploadedFileDTO
    commit: bool = False


class RenameRowDTO(BaseDTO):
    factory_code: FactoryCode
    yarn_code: str
    old_name: str
    new_name: str
    reason: str
    old_loss_group: str = ""
    new_loss_group: str = ""


class RenameImportResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    valid: list[RenameRowDTO] = []
    rejected_rows: list[RejectedRowDTO] = []


# ---- UC-71 ----
class NormalizeNamesRequest(BaseRequestDTO):
    commit: bool = False


class NameChangeDTO(BaseDTO):
    factory_code: FactoryCode
    yarn_code: str
    old_name: str
    new_name: str


class DuplicateDecisionDTO(BaseDTO):
    factory_code: FactoryCode
    upper_name: str
    yarn_code: str
    yarn_name: str
    status: YarnStatus
    keep: bool
    keep_code: str
    accounting_codes: list[str] = []
    reason: str = ""


class NormalizeNamesResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    rename_count: int = 0
    group_count: int = 0
    keep_count: int = 0
    drop_count: int = 0
    drop_with_code_count: int = 0
    changes: list[NameChangeDTO] = []
    decisions: list[DuplicateDecisionDTO] = []
    plan_file: FileDownloadDTO | None = None

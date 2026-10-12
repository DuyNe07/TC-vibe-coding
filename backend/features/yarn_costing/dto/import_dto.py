"""DTOs of UC-33..UC-35 and UC-41 (file mẫu, nhập file, đối chiếu giá cũ, các lần nhập)."""

from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, FileDownloadDTO, UploadedFileDTO
from backend.features.yarn_costing.dto.common_dto import ActorDTO
from backend.features.yarn_costing.models.enums import FactoryCode, ImportMode


class DownloadTemplateRequest(BaseRequestDTO):
    factory_code: FactoryCode


class ImportWorkbookRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    mode: ImportMode
    cutoff_date: date
    file: UploadedFileDTO
    commit: bool = False


class SheetResultDTO(BaseDTO):
    sheet: str
    read: int = 0
    created: int = 0
    updated: int = 0
    rejected: int = 0
    skipped_message: str = ""


class RejectedRowDTO(BaseDTO):
    sheet: str
    excel_row: int
    key: str = ""
    reason: str


class ImportResultResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    sheets: list[SheetResultDTO] = []
    rejected_rows: list[RejectedRowDTO] = []
    valid_count: int = 0
    import_id: str | None = None
    result_file: FileDownloadDTO | None = None


class GetLegacyComparisonRequest(BaseRequestDTO):
    import_id: str
    only_mismatch: bool = False


class LegacyComparisonRowDTO(BaseDTO):
    yarn_code: str
    yarn_name: str = ""
    old_total: Decimal
    app_total: Decimal | None = None
    diff_vnd: Decimal | None = None
    diff_percent: Decimal | None = None
    old_labor: Decimal
    old_depreciation: Decimal
    old_electricity: Decimal
    old_materials: Decimal
    old_overhead: Decimal
    new_labor: Decimal | None = None
    new_depreciation: Decimal | None = None
    new_electricity: Decimal | None = None
    new_materials: Decimal | None = None
    new_overhead: Decimal | None = None
    status: str = ""
    matched: bool = False


class LegacyComparisonResponse(BaseResponseDTO):
    items: list[LegacyComparisonRowDTO] = []
    matched_count: int = 0
    mismatched_count: int = 0
    not_priced_count: int = 0
    file: FileDownloadDTO


class ListImportBatchesRequest(BaseRequestDTO):
    factory_code: FactoryCode | None = None


class ImportBatchDTO(BaseDTO):
    import_id: str
    factory_code: FactoryCode
    mode: ImportMode
    cutoff_date: date
    file_name: str
    imported_by: str = ""
    imported_at: datetime
    created_count: int = 0
    updated_count: int = 0
    rejected_count: int = 0
    sheets: list[SheetResultDTO] = []


class ImportBatchListResponse(BaseResponseDTO):
    items: list[ImportBatchDTO] = []


# ---- UC-44 / UC-45 Khai báo thành phần sợi pha (5.7) ----
class DownloadComponentTemplateRequest(BaseRequestDTO):
    factory_code: FactoryCode


class ImportComponentFileRequest(BaseRequestDTO):
    actor: ActorDTO
    factory_code: FactoryCode
    file: UploadedFileDTO
    effective_date: date | None = None
    reason: str = ""
    commit: bool = False


class ComponentGroupResultDTO(BaseDTO):
    excel_row: int
    group_key: str
    created: bool = False
    old_level: str = ""
    new_level: str
    components_text: str = ""  # "PE 48%; MODAL 52%"
    old_losses: dict[str, Decimal] = {}
    new_losses: dict[str, Decimal] = {}
    affected_count: int = 0


class UnmatchedYarnDTO(BaseDTO):
    yarn_code: str
    yarn_name: str = ""
    material_label: str
    carding_stage: str
    group_key: str


class ComponentImportResponse(BaseResponseDTO):
    message: str
    committed: bool = False
    valid_count: int = 0
    created_count: int = 0
    rejected_count: int = 0
    affected_count: int = 0
    unmatched_count: int = 0
    groups: list[ComponentGroupResultDTO] = []
    rejected_rows: list[RejectedRowDTO] = []
    unmatched: list[UnmatchedYarnDTO] = []
    stage_codes: list[str] = []
    import_id: str | None = None
    batch_id: str | None = None
    result_file: FileDownloadDTO | None = None

"""DTOs of UC-01..UC-04 (fabric data), UC-26 (labels) and UC-39 (import history)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, UploadedFileDTO
from backend.features.woven_costing.models.enums import FabricSource, ImportResult, YarnDirection, YarnKind


class PreviewFabricImportRequest(BaseRequestDTO):
    files: list[UploadedFileDTO] = Field(default_factory=list)


class FileCountDTO(BaseDTO):
    file_name: str
    kind: str
    count: int


class FabricImportRowDTO(BaseDTO):
    tcfno: str
    fabric_name: str = ""
    source: str = ""
    result: ImportResult
    reason: str = ""


class FabricImportPreviewResponse(BaseResponseDTO):
    file_names: list[str] = Field(default_factory=list)
    file_counts: list[FileCountDTO] = Field(default_factory=list)
    new_count: int = 0
    changed_count: int = 0
    unchanged_count: int = 0
    missing_yarn_count: int = 0
    error_count: int = 0
    rows: list[FabricImportRowDTO] = Field(default_factory=list)


class FabricImportSaveResponse(BaseResponseDTO):
    new_count: int = 0
    changed_count: int = 0
    missing_yarn_count: int = 0
    message: str


class FabricYarnDTO(BaseDTO):
    direction: YarnDirection
    seq: int = 1
    full_yarn_name: str = ""
    yarn_code: str = ""
    yarn_name: str = ""
    rate: Decimal = Decimal(0)
    yarn_kind: YarnKind | None = None
    raw_yarn_code: str = ""
    raw_yarn_name: str = ""
    raw_rate: Decimal | None = None
    twist_tpm: str = ""


class FabricSpecsDTO(BaseDTO):
    greige_width_cm: Decimal | None = None
    greige_cut_width_cm: Decimal | None = None
    greige_gsm: Decimal | None = None
    greige_g_per_m: Decimal | None = None
    greige_warp_density: Decimal | None = None
    greige_weft_density: Decimal | None = None
    finished_width_cm: Decimal | None = None
    finished_cut_width_cm: Decimal | None = None
    finished_gsm: Decimal | None = None
    finished_g_per_m: Decimal | None = None
    finished_warp_density: Decimal | None = None
    finished_weft_density: Decimal | None = None
    warping_loss_rate: Decimal | None = None


class SaveFabricRequest(BaseRequestDTO):
    is_new: bool = True
    tcfno: str
    fabric_name: str = ""
    remark: str = ""
    warping_loss_rate: Decimal | None = None
    greige_width_cm: Decimal | None = None
    greige_cut_width_cm: Decimal | None = None
    greige_gsm: Decimal | None = None
    greige_g_per_m: Decimal | None = None
    greige_warp_density: Decimal | None = None
    greige_weft_density: Decimal | None = None
    finished_width_cm: Decimal | None = None
    finished_cut_width_cm: Decimal | None = None
    finished_gsm: Decimal | None = None
    finished_g_per_m: Decimal | None = None
    finished_warp_density: Decimal | None = None
    finished_weft_density: Decimal | None = None
    yarns: list[FabricYarnDTO] = Field(default_factory=list)


class SaveFabricResponse(BaseResponseDTO):
    tcfno: str
    message: str


class SearchFabricsRequest(BaseRequestDTO):
    keyword: str = ""
    source: FabricSource | None = None
    missing_yarn_only: bool = False
    selected_tcfno: str | None = None


class FabricRowDTO(BaseDTO):
    tcfno: str
    fabric_name: str
    source: FabricSource
    greige_width_cm: Decimal | None = None
    greige_warp_density: Decimal | None = None
    greige_weft_density: Decimal | None = None
    greige_g_per_m: Decimal | None = None
    finished_width_cm: Decimal | None = None
    finished_g_per_m: Decimal | None = None
    shrinkage: Decimal | None = None
    warping_loss_rate: Decimal | None = None
    created_date: date | None = None
    updated_at: datetime | None = None


class FabricDetailDTO(FabricSpecsDTO):
    tcfno: str
    tcfno_raw: str = ""
    sy_item: str = ""
    fabric_name: str = ""
    structure: str = ""
    fabric_kind: str = ""
    tcfno_status: str = ""
    created_date: date | None = None
    in_charge: str = ""
    greige_shrink_warp: Decimal | None = None
    greige_shrink_weft: Decimal | None = None
    finished_shrink_warp: Decimal | None = None
    finished_shrink_weft: Decimal | None = None
    source: FabricSource
    remark: str = ""
    updated_at: datetime | None = None
    updated_by: str = ""
    yarns: list[FabricYarnDTO] = Field(default_factory=list)


class SearchFabricsResponse(BaseResponseDTO):
    total: int = 0
    rows: list[FabricRowDTO] = Field(default_factory=list)
    detail: FabricDetailDTO | None = None


class LabelInputDTO(BaseDTO):
    tcfno: str
    remark: str = ""


class PrintLabelRequest(BaseRequestDTO):
    labels: list[LabelInputDTO] = Field(default_factory=list)


class FabricImportLogDTO(BaseDTO):
    imported_at: datetime
    imported_by: str
    file_names: str
    new_count: int = 0
    changed_count: int = 0
    unchanged_count: int = 0
    missing_yarn_count: int = 0
    error_count: int = 0


class FabricImportLogResponse(BaseResponseDTO):
    rows: list[FabricImportLogDTO] = Field(default_factory=list)

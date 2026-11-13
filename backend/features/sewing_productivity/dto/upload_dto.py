"""UC-01, UC-02, UC-03: checking and saving the data file, upload history."""

from datetime import date, datetime

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, UploadedFileDTO


class CheckUploadRequest(BaseRequestDTO):
    file: UploadedFileDTO


class SkippedRowDTO(BaseDTO):
    sheet: str
    row_number: int
    reason: str


class UploadWarningDTO(BaseDTO):
    kind: str
    warning_date: date | None = None
    count: int
    detail: str = ""


class UploadCheckResponse(BaseResponseDTO):
    """`read_rows`, `valid_rows`, `skipped_rows` count the `Production data` sheet; `skipped` also lists `Target system`."""

    read_rows: int
    valid_rows: int
    skipped_rows: int
    target_skipped_rows: int = 0
    from_date: date | None = None
    to_date: date | None = None
    stored_rows_in_range: int
    skipped: list[SkippedRowDTO]
    warnings: list[UploadWarningDTO]
    can_save: bool


class SaveUploadRequest(BaseRequestDTO):
    file: UploadedFileDTO


class SaveUploadResponse(BaseResponseDTO):
    saved_rows: int
    to_date: date | None = None
    message: str


class UploadSheetCountDTO(BaseDTO):
    sheet: str
    read_rows: int
    valid_rows: int
    skipped_rows: int


class UploadChangeCountDTO(BaseDTO):
    sheet: str
    factory: str
    added: int
    updated: int
    hidden: int


class UploadLogDTO(BaseDTO):
    """UC-03 one upload. Totals and details (BR-72 to BR-74) are None / empty when `has_details` is False (an upload
    saved before 2026-11-09)."""

    uploaded_at: datetime
    uploaded_by: str
    file_name: str
    from_date: date | None = None
    to_date: date | None = None
    saved_rows: int
    skipped_rows: int
    status: str = "Saved"
    reject_reason: str = ""
    has_details: bool = False
    added: int | None = None
    updated: int | None = None
    hidden: int | None = None
    sheet_counts: list[UploadSheetCountDTO] = []
    changes: list[UploadChangeCountDTO] = []
    skipped: list[SkippedRowDTO] = []
    warnings: list[UploadWarningDTO] = []


class UploadLogListResponse(BaseResponseDTO):
    items: list[UploadLogDTO]

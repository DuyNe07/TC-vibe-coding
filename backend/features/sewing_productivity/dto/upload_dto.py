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


class UploadLogDTO(BaseDTO):
    uploaded_at: datetime
    uploaded_by: str
    file_name: str
    from_date: date
    to_date: date
    saved_rows: int
    skipped_rows: int


class UploadLogListResponse(BaseResponseDTO):
    items: list[UploadLogDTO]

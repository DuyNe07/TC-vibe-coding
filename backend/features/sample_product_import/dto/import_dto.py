"""Contracts of UC-02 (preview_import) and UC-03 (commit_import)."""

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO, UploadedFileDTO
from backend.features.sample_product_import.models.import_row import ImportAction

__all__ = [
    "CommitImportRequest",
    "CommitImportResponse",
    "ImportAction",
    "ImportRowResultDTO",
    "PreviewImportRequest",
    "PreviewImportResponse",
]


class PreviewImportRequest(BaseRequestDTO):
    file: UploadedFileDTO


class CommitImportRequest(BaseRequestDTO):
    file: UploadedFileDTO


class ImportRowResultDTO(BaseDTO):
    row_number: int
    code: str
    name: str
    unit: str
    quantity: float | None
    unit_price: float | None
    action: ImportAction
    errors: list[str]


class PreviewImportResponse(BaseResponseDTO):
    rows: list[ImportRowResultDTO]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    create_count: int
    update_count: int


class CommitImportResponse(BaseResponseDTO):
    created: int
    updated: int
    rejected: int
    rejected_rows: list[ImportRowResultDTO]

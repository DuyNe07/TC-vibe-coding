"""Upload check and history -> response DTOs."""

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.dto.upload_dto import (
    SkippedRowDTO,
    UploadCheckResponse,
    UploadLogDTO,
    UploadLogListResponse,
    UploadWarningDTO,
)
from backend.features.sewing_productivity.models.settings_records import UploadLog
from backend.features.sewing_productivity.models.upload_values import ParsedUpload, UploadWarning


class UploadCheckResponseBuilder(BaseBuilder[UploadCheckResponse]):
    def __init__(self, parsed: ParsedUpload, warnings: list[UploadWarning], stored_rows_in_range: int) -> None:
        self.parsed = parsed
        self.warnings = warnings
        self.stored_rows_in_range = stored_rows_in_range

    def build(self) -> UploadCheckResponse:
        parsed = self.parsed
        return UploadCheckResponse(
            read_rows=parsed.production_read,
            valid_rows=len(parsed.production),
            skipped_rows=parsed.production_skipped,
            target_skipped_rows=len(parsed.skipped) - parsed.production_skipped,
            from_date=parsed.production_range.from_date,
            to_date=parsed.production_range.to_date,
            stored_rows_in_range=self.stored_rows_in_range,
            skipped=[
                SkippedRowDTO(sheet=row.sheet, row_number=row.row_number, reason=row.reason) for row in parsed.skipped
            ],
            warnings=[
                UploadWarningDTO(kind=item.kind, warning_date=item.warning_date, count=item.count, detail=item.detail)
                for item in self.warnings
            ],
            can_save=True,
        )


class UploadLogListBuilder(BaseBuilder[UploadLogListResponse]):
    def __init__(self, logs: list[UploadLog]) -> None:
        self.logs = logs

    def build(self) -> UploadLogListResponse:
        ordered = sorted(self.logs, key=lambda log: log.uploaded_at, reverse=True)
        return UploadLogListResponse(
            items=[
                UploadLogDTO(
                    uploaded_at=log.uploaded_at,
                    uploaded_by=log.uploaded_by,
                    file_name=log.file_name,
                    from_date=log.from_date,
                    to_date=log.to_date,
                    saved_rows=log.saved_rows,
                    skipped_rows=log.skipped_rows,
                )
                for log in ordered
            ]
        )

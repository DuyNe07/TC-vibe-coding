"""Upload check and history -> response DTOs."""

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.dto.upload_dto import (
    SkippedRowDTO,
    UploadChangeCountDTO,
    UploadCheckResponse,
    UploadLogDTO,
    UploadLogListResponse,
    UploadSheetCountDTO,
    UploadWarningDTO,
)
from backend.features.sewing_productivity.models.settings_records import UploadLog
from backend.features.sewing_productivity.models.upload_values import ParsedUpload, StrengthUpload, UploadWarning


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


class StrengthCheckResponseBuilder(BaseBuilder[UploadCheckResponse]):
    """UC-33 a Line Strength file checked: lines read, kept, skipped; no dates, no warnings."""

    def __init__(self, upload: StrengthUpload, stored_lines: int) -> None:
        self.upload = upload
        self.stored_lines = stored_lines

    def build(self) -> UploadCheckResponse:
        upload = self.upload
        return UploadCheckResponse(
            read_rows=upload.read_rows,
            valid_rows=len(upload.lines),
            skipped_rows=len(upload.skipped),
            stored_rows_in_range=self.stored_lines,
            skipped=[
                SkippedRowDTO(sheet=row.sheet, row_number=row.row_number, reason=row.reason) for row in upload.skipped
            ],
            warnings=[],
            can_save=True,
        )


class UploadLogListBuilder(BaseBuilder[UploadLogListResponse]):
    def __init__(self, logs: list[UploadLog]) -> None:
        self.logs = logs

    def build(self) -> UploadLogListResponse:
        ordered = sorted(self.logs, key=lambda log: log.uploaded_at, reverse=True)
        return UploadLogListResponse(items=[self._item(log) for log in ordered])

    @staticmethod
    def _total(log: UploadLog, field: str) -> int | None:
        """The BR-73 total of one kind of change; None for an upload saved before the details existed."""
        return sum(getattr(change, field) for change in log.changes) if log.has_details else None

    def _item(self, log: UploadLog) -> UploadLogDTO:
        return UploadLogDTO(
            uploaded_at=log.uploaded_at,
            uploaded_by=log.uploaded_by,
            file_name=log.file_name,
            from_date=log.from_date,
            to_date=log.to_date,
            saved_rows=log.saved_rows,
            skipped_rows=log.skipped_rows,
            status=log.status.value,
            reject_reason=log.reject_reason,
            has_details=log.has_details,
            added=self._total(log, "added"),
            updated=self._total(log, "updated"),
            hidden=self._total(log, "hidden"),
            sheet_counts=[UploadSheetCountDTO(**count.model_dump()) for count in log.sheet_counts],
            changes=[
                UploadChangeCountDTO(
                    sheet=change.sheet,
                    factory=change.factory.value,
                    added=change.added,
                    updated=change.updated,
                    hidden=change.hidden,
                )
                for change in log.changes
            ],
            skipped=[SkippedRowDTO(**row.model_dump()) for row in log.skipped],
            warnings=[UploadWarningDTO(**item.model_dump()) for item in log.warnings],
        )

"""BR-72, BR-73, BR-74: what the upload history keeps of each upload, saved or rejected."""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import datetime

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.constants import (
    SHEET_LINE_STRENGTH,
    SHEET_PRODUCTION,
    SHEET_TARGET,
    SHEET_WORKER,
    SHEET_WORKER_DERIVED,
    SKIPPED_ROWS_KEPT,
)
from backend.features.sewing_productivity.models.enums import Factory, UploadStatus
from backend.features.sewing_productivity.models.settings_records import (
    UploadChangeCount,
    UploadLog,
    UploadSheetCount,
    UploadSkippedNote,
    UploadWarningNote,
)
from backend.features.sewing_productivity.models.source_records import (
    LineStrength,
    ProductionRecord,
    TargetRecord,
    WorkerRecord,
)
from backend.features.sewing_productivity.models.upload_values import ParsedUpload, StrengthUpload, UploadWarning

SourceRecord = ProductionRecord | TargetRecord | WorkerRecord | LineStrength


class UploadTrackingBusiness(BaseBusiness[UploadLog]):
    def sheet_counts(self, parsed: ParsedUpload) -> list[UploadSheetCount]:
        """BR-72 rows read, valid and skipped per sheet. A Worker row is one factory on one day."""
        target_skipped = sum(1 for row in parsed.skipped if row.sheet == SHEET_TARGET)
        return [
            UploadSheetCount(
                sheet=SHEET_PRODUCTION,
                read_rows=parsed.production_read,
                valid_rows=len(parsed.production),
                skipped_rows=parsed.production_skipped,
            ),
            UploadSheetCount(
                sheet=SHEET_TARGET,
                read_rows=len(parsed.targets) + target_skipped,
                valid_rows=len(parsed.targets),
                skipped_rows=target_skipped,
            ),
            UploadSheetCount(
                sheet=SHEET_WORKER_DERIVED if parsed.derived_workers else SHEET_WORKER,  # BR-97
                read_rows=len(parsed.workers),
                valid_rows=len(parsed.workers),
                skipped_rows=0,
            ),
        ]

    def change_counts(
        self, sheet: str, active_ids: set[str], writes: Iterable[SourceRecord]
    ) -> list[UploadChangeCount]:
        """BR-73 per factory: a written row flagged deleted is hidden; one already shown is updated; any other row
        (new, or hidden before and back in the file) is added. Unchanged rows are never written, so never counted."""
        counts: dict[Factory, dict[str, int]] = defaultdict(lambda: {"added": 0, "updated": 0, "hidden": 0})
        for row in writes:
            if row.is_deleted:
                kind = "hidden"
            elif row.id in active_ids:
                kind = "updated"
            else:
                kind = "added"
            counts[row.factory][kind] += 1
        return [
            UploadChangeCount(sheet=sheet, factory=factory, **numbers)
            for factory, numbers in sorted(counts.items(), key=lambda item: list(Factory).index(item[0]))
        ]

    def saved_log(
        self,
        *,
        uploaded_at: datetime,
        uploaded_by: str,
        file_name: str,
        parsed: ParsedUpload,
        changes: Sequence[UploadChangeCount],
        warnings: Sequence[UploadWarning],
    ) -> UploadLog:
        """BR-72, BR-73 the history row of a saved upload, with its details."""
        return UploadLog(
            uploaded_at=uploaded_at,
            uploaded_by=uploaded_by,
            file_name=file_name,
            from_date=parsed.production_range.from_date,
            to_date=parsed.production_range.to_date,
            saved_rows=len(parsed.production),
            skipped_rows=len(parsed.skipped),
            status=UploadStatus.SAVED,
            has_details=True,
            sheet_counts=self.sheet_counts(parsed),
            changes=list(changes),
            skipped=[
                UploadSkippedNote(sheet=row.sheet, row_number=row.row_number, reason=row.reason)
                for row in parsed.skipped[:SKIPPED_ROWS_KEPT]
            ],
            warnings=[
                UploadWarningNote(kind=item.kind, warning_date=item.warning_date, count=item.count, detail=item.detail)
                for item in warnings
            ],
        )

    @staticmethod
    def strength_log(
        *,
        uploaded_at: datetime,
        uploaded_by: str,
        file_name: str,
        upload: StrengthUpload,
        changes: Sequence[UploadChangeCount],
    ) -> UploadLog:
        """BR-82 the history row of a saved Line Strength file: one sheet, the lines added / updated / hidden."""
        return UploadLog(
            uploaded_at=uploaded_at,
            uploaded_by=uploaded_by,
            file_name=file_name,
            saved_rows=len(upload.lines),
            skipped_rows=len(upload.skipped),
            status=UploadStatus.SAVED,
            has_details=True,
            sheet_counts=[
                UploadSheetCount(
                    sheet=SHEET_LINE_STRENGTH,
                    read_rows=upload.read_rows,
                    valid_rows=len(upload.lines),
                    skipped_rows=len(upload.skipped),
                )
            ],
            changes=list(changes),
            skipped=[
                UploadSkippedNote(sheet=row.sheet, row_number=row.row_number, reason=row.reason)
                for row in upload.skipped[:SKIPPED_ROWS_KEPT]
            ],
        )

    @staticmethod
    def rejected_log(*, uploaded_at: datetime, uploaded_by: str, file_name: str, reason: str) -> UploadLog:
        """BR-74 the history row of a refused file: who, when, which file, the exact sentence shown. Nothing saved."""
        return UploadLog(
            uploaded_at=uploaded_at,
            uploaded_by=uploaded_by,
            file_name=file_name,
            saved_rows=0,
            skipped_rows=0,
            status=UploadStatus.REJECTED,
            reject_reason=reason,
            has_details=True,
        )

    @staticmethod
    def counts_as_last_upload(log: UploadLog) -> bool:
        """BR-74 a rejected upload is not the "Last file upload" of the reports."""
        return log.status == UploadStatus.SAVED

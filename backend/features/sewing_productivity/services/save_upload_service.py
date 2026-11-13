"""UC-02: save the data file, each sheet over its own date range (BR-07), and keep the whole upload in the history:
counts per sheet, skipped rows, warnings, rows added / updated / hidden per factory (BR-72, BR-73). A file refused
here is kept in the history as rejected (BR-74)."""

from collections.abc import Callable
from datetime import date
from typing import TypeVar

from backend.core.base import BaseRepository, BaseService, UploadedFileDTO, utc_now
from backend.core.exceptions import AppError
from backend.features.sewing_productivity.builders.strength_read_builders import LineStrengthReadBuilder
from backend.features.sewing_productivity.builders.upload_read_builders import RawWorkbookBuilder, WorkbookSheetsBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.catalog_business import CatalogBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.line_strength_business import LineStrengthBusiness
from backend.features.sewing_productivity.business.upload_business import UploadBusiness
from backend.features.sewing_productivity.business.upload_tracking_business import UploadTrackingBusiness
from backend.features.sewing_productivity.constants import (
    MESSAGE_STRENGTH_SAVED,
    SHEET_LINE_STRENGTH,
    SHEET_PRODUCTION,
    SHEET_TARGET,
    SHEET_WORKER,
)
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest, SaveUploadResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.models.settings_records import UploadChangeCount
from backend.features.sewing_productivity.models.source_records import ProductionRecord, TargetRecord, WorkerRecord
from backend.features.sewing_productivity.models.upload_values import (
    DateRange,
    ParsedUpload,
    StrengthUpload,
    UploadFileFacts,
    UploadWarning,
)
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source
from backend.features.sewing_productivity.repositories.source_repositories import (
    LineStrengthRepository,
    ProductionRecordRepository,
    TargetRecordRepository,
    UploadLogRepository,
    WorkerRecordRepository,
)

TRecord = TypeVar("TRecord", ProductionRecord, TargetRecord, WorkerRecord)


class SaveUploadService(BaseService[SaveUploadRequest, SaveUploadResponse]):
    def __init__(
        self,
        production: ProductionRecordRepository | None = None,
        targets: TargetRecordRepository | None = None,
        workers: WorkerRecordRepository | None = None,
        logs: UploadLogRepository | None = None,
        loader: Callable[[], ReportSource] = load_report_source,
        strength_lines: LineStrengthRepository | None = None,
    ) -> None:
        self.strength_lines = strength_lines or LineStrengthRepository()
        self.strengths = LineStrengthBusiness()
        self.production = production or ProductionRecordRepository()
        self.targets = targets or TargetRecordRepository()
        self.workers = workers or WorkerRecordRepository()
        self.logs = logs or UploadLogRepository()
        self.loader = loader
        self.access = AccessBusiness()
        self.uploads = UploadBusiness()
        self.tracking = UploadTrackingBusiness()
        self.cleaning = CleaningBusiness()
        self.catalogs = CatalogBusiness()

    def execute(self, request: SaveUploadRequest) -> SaveUploadResponse:
        user = self.current_user
        self.access.ensure_valid(user)  # BR-09 first: a refused person leaves no history row (BR-74)
        file = request.file
        saved_by = self.access.saved_by(user)
        try:
            parsed = self._read(file)
        except AppError as exc:
            self.logs.add(
                self.tracking.rejected_log(
                    uploaded_at=utc_now(), uploaded_by=saved_by, file_name=file.filename, reason=exc.message
                )
            )
            self.logger.info("Rejected %s: %s", file.filename, exc.message)
            raise
        who = self.access.deleted_by(user)
        if isinstance(parsed, StrengthUpload):
            return self._save_strength(parsed, file.filename, saved_by, who)
        warnings = self._warnings(parsed)
        changes = [
            *self._replace(
                SHEET_PRODUCTION,
                self.production,
                parsed.production,
                parsed.production_range,
                lambda row: row.production_date,
                who,
            ),
            *self._replace(
                SHEET_TARGET, self.targets, parsed.targets, parsed.target_range, lambda row: row.target_date, who
            ),
            *self._replace(
                SHEET_WORKER, self.workers, parsed.workers, parsed.worker_range, lambda row: row.work_date, who
            ),
        ]
        date_range = parsed.production_range
        self.logs.add(
            self.tracking.saved_log(
                uploaded_at=utc_now(),
                uploaded_by=saved_by,
                file_name=file.filename,
                parsed=parsed,
                changes=changes,
                warnings=warnings,
            )
        )
        self.logger.info(
            "Saved %s: %s change rows, %s warnings, %s skipped", file.filename, len(changes), len(warnings),
            len(parsed.skipped),
        )  # fmt: skip
        message = f"Đã lưu {len(parsed.production)} dòng, dữ liệu đến ngày {date_range.to_date:%d/%m/%Y}."
        return SaveUploadResponse(saved_rows=len(parsed.production), to_date=date_range.to_date, message=message)

    def _read(self, file: UploadedFileDTO) -> ParsedUpload | StrengthUpload:
        """BR-01 to BR-06, BR-16: the checks of UC-01, done again before writing anything; a workbook without the data
        sheets may be a Line Strength file (UC-33, BR-81)."""
        self.uploads.ensure_file(UploadFileFacts(extension=file.extension, size_mb=file.size_mb))
        sheets = WorkbookSheetsBuilder(file).build()
        if not sheets:
            raw = LineStrengthReadBuilder(file).build()
            if self.strengths.is_strength_file(set(sheets), raw):
                return self.strengths.read(raw, file.filename)
        production_only = self.uploads.ensure_sheets(set(sheets))  # BR-97 a past-year file
        return self.uploads.parse(RawWorkbookBuilder(file, sheets).build(), production_only)

    def _save_strength(
        self, upload: StrengthUpload, file_name: str, saved_by: str, who: str | None
    ) -> SaveUploadResponse:
        """UC-33: the file replaces every line strength (BR-82), the history keeps the upload (BR-72, BR-73)."""
        stored = self.strength_lines.list_all()
        writes = self.strengths.replacement_writes(stored, self.strength_lines.list_deleted(), upload.lines, who)
        if writes:
            self.strength_lines.save_many(writes)
        changes = self.tracking.change_counts(SHEET_LINE_STRENGTH, {row.id for row in stored}, writes)
        self.logs.add(
            self.tracking.strength_log(
                uploaded_at=utc_now(), uploaded_by=saved_by, file_name=file_name, upload=upload, changes=changes
            )
        )
        self.logger.info("Saved Line Strength %s: %s lines, %s rows written", file_name, len(upload.lines), len(writes))
        message = MESSAGE_STRENGTH_SAVED.format(count=len(upload.lines))
        return SaveUploadResponse(saved_rows=len(upload.lines), message=message)

    def _warnings(self, parsed: ParsedUpload) -> list[UploadWarning]:
        """BR-08 / BR-72 the warnings shown after the save, computed as UC-01 does (on the data once saved)."""
        source = self.loader()
        production = self.uploads.state_after_save(
            source.production, parsed.production, parsed.production_range, lambda row: row.production_date
        )
        targets = self.uploads.state_after_save(
            source.targets, parsed.targets, parsed.target_range, lambda row: row.target_date
        )
        workers = self.uploads.state_after_save(
            source.workers, parsed.workers, parsed.worker_range, lambda row: row.work_date
        )
        lookup = self.cleaning.name_lookup(production, targets)
        return self.catalogs.warnings(self.cleaning.clean(parsed.production, lookup, source.catalogs), workers, targets)

    def _replace(
        self,
        sheet: str,
        repository: BaseRepository[TRecord],
        incoming: list[TRecord],
        date_range: DateRange,
        date_of: Callable[[TRecord], date],
        who: str | None,
    ) -> list[UploadChangeCount]:
        """The same steps for the 3 tables. Nothing is written when nothing changed. Returns BR-73 per factory."""
        stored = repository.list_all()
        writes = self.uploads.replacement_writes(stored, repository.list_deleted(), incoming, date_range, date_of, who)
        if writes:
            repository.save_many(writes)
        return self.tracking.change_counts(sheet, {row.id for row in stored}, writes)

"""UC-01: check the data file. No data is saved; a refused file is kept in the upload history as rejected (BR-74).
UC-33: the same button checks a Line Strength file (BR-81)."""

from collections.abc import Callable

from backend.core.base import BaseService, UploadedFileDTO, utc_now
from backend.core.exceptions import AppError
from backend.features.sewing_productivity.builders.strength_read_builders import LineStrengthReadBuilder
from backend.features.sewing_productivity.builders.upload_read_builders import RawWorkbookBuilder, WorkbookSheetsBuilder
from backend.features.sewing_productivity.builders.upload_response_builders import (
    StrengthCheckResponseBuilder,
    UploadCheckResponseBuilder,
)
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.catalog_business import CatalogBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.line_strength_business import LineStrengthBusiness
from backend.features.sewing_productivity.business.upload_business import UploadBusiness
from backend.features.sewing_productivity.business.upload_tracking_business import UploadTrackingBusiness
from backend.features.sewing_productivity.dto.upload_dto import CheckUploadRequest, UploadCheckResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.models.upload_values import ParsedUpload, StrengthUpload, UploadFileFacts
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source
from backend.features.sewing_productivity.repositories.source_repositories import (
    LineStrengthRepository,
    UploadLogRepository,
)


class CheckUploadService(BaseService[CheckUploadRequest, UploadCheckResponse]):
    def __init__(
        self,
        loader: Callable[[], ReportSource] = load_report_source,
        logs: UploadLogRepository | None = None,
        strength_lines: LineStrengthRepository | None = None,
    ) -> None:
        self.loader = loader
        self.logs = logs or UploadLogRepository()
        self.strength_lines = strength_lines or LineStrengthRepository()
        self.strengths = LineStrengthBusiness()
        self.access = AccessBusiness()
        self.uploads = UploadBusiness()
        self.cleaning = CleaningBusiness()
        self.catalogs = CatalogBusiness()
        self.tracking = UploadTrackingBusiness()

    def execute(self, request: CheckUploadRequest) -> UploadCheckResponse:
        user = self.current_user
        self.access.ensure_valid(user)  # BR-09 first: a refused person leaves no history row (BR-74)
        file = request.file
        try:
            parsed = self._read(file)
        except AppError as exc:
            self.logs.add(
                self.tracking.rejected_log(
                    uploaded_at=utc_now(),
                    uploaded_by=self.access.saved_by(user),
                    file_name=file.filename,
                    reason=exc.message,
                )
            )
            self.logger.info("Rejected %s: %s", file.filename, exc.message)
            raise
        if isinstance(parsed, StrengthUpload):  # UC-33 a Line Strength file: nothing saved yet
            self.logger.info("Checked Line Strength %s: %s lines, %s skipped", file.filename, len(parsed.lines),
                             len(parsed.skipped))  # fmt: skip
            return StrengthCheckResponseBuilder(parsed, self.strength_lines.count()).build()
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
        warnings = self.catalogs.warnings(
            self.cleaning.clean(parsed.production, lookup, source.catalogs), workers, targets
        )
        stored = sum(
            1 for row in source.production if self.uploads.is_in_range(row.production_date, parsed.production_range)
        )
        self.logger.info(
            "Checked %s: valid=%s skipped=%s warnings=%s stored_in_range=%s",
            file.filename, len(parsed.production), len(parsed.skipped), len(warnings), stored,
        )  # fmt: skip
        return UploadCheckResponseBuilder(parsed, warnings, stored).build()

    def _read(self, file: UploadedFileDTO) -> ParsedUpload | StrengthUpload:
        """BR-01 to BR-06, BR-16; a workbook without the data sheets may be a Line Strength file (UC-33, BR-81)."""
        self.uploads.ensure_file(UploadFileFacts(extension=file.extension, size_mb=file.size_mb))
        sheets = WorkbookSheetsBuilder(file).build()
        if not sheets:
            raw = LineStrengthReadBuilder(file).build()
            if self.strengths.is_strength_file(set(sheets), raw):
                return self.strengths.read(raw, file.filename)
        production_only = self.uploads.ensure_sheets(set(sheets))  # BR-97 a past-year file
        return self.uploads.parse(RawWorkbookBuilder(file, sheets).build(), production_only)

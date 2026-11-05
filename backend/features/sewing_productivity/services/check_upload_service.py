"""UC-01: check the data file. Nothing is saved."""

from collections.abc import Callable

from backend.core.base import BaseService
from backend.features.sewing_productivity.builders.upload_read_builders import RawWorkbookBuilder, WorkbookSheetsBuilder
from backend.features.sewing_productivity.builders.upload_response_builders import UploadCheckResponseBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.catalog_business import CatalogBusiness
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.upload_business import UploadBusiness
from backend.features.sewing_productivity.dto.upload_dto import CheckUploadRequest, UploadCheckResponse
from backend.features.sewing_productivity.models.clean_values import ReportSource
from backend.features.sewing_productivity.models.upload_values import UploadFileFacts
from backend.features.sewing_productivity.repositories.report_source_loader import load_report_source


class CheckUploadService(BaseService[CheckUploadRequest, UploadCheckResponse]):
    def __init__(self, loader: Callable[[], ReportSource] = load_report_source) -> None:
        self.loader = loader
        self.access = AccessBusiness()
        self.uploads = UploadBusiness()
        self.cleaning = CleaningBusiness()
        self.catalogs = CatalogBusiness()

    def execute(self, request: CheckUploadRequest) -> UploadCheckResponse:
        self.access.ensure_valid(self.current_user)
        file = request.file
        self.uploads.ensure_file(UploadFileFacts(extension=file.extension, size_mb=file.size_mb))
        sheets = WorkbookSheetsBuilder(file).build()
        self.uploads.ensure_sheets(set(sheets))
        parsed = self.uploads.parse(RawWorkbookBuilder(file, sheets).build())
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

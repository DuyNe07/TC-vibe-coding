"""UC-02: save the data file, each sheet over its own date range (BR-07)."""

from collections.abc import Callable
from datetime import date
from typing import TypeVar

from backend.core.base import BaseRepository, BaseService, utc_now
from backend.features.sewing_productivity.builders.upload_read_builders import RawWorkbookBuilder, WorkbookSheetsBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.business.upload_business import UploadBusiness
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest, SaveUploadResponse
from backend.features.sewing_productivity.models.settings_records import UploadLog
from backend.features.sewing_productivity.models.stored_record import StoredRecord
from backend.features.sewing_productivity.models.upload_values import DateRange, UploadFileFacts
from backend.features.sewing_productivity.repositories.source_repositories import (
    ProductionRecordRepository,
    TargetRecordRepository,
    UploadLogRepository,
    WorkerRecordRepository,
)

TRecord = TypeVar("TRecord", bound=StoredRecord)


class SaveUploadService(BaseService[SaveUploadRequest, SaveUploadResponse]):
    def __init__(
        self,
        production: ProductionRecordRepository | None = None,
        targets: TargetRecordRepository | None = None,
        workers: WorkerRecordRepository | None = None,
        logs: UploadLogRepository | None = None,
    ) -> None:
        self.production = production or ProductionRecordRepository()
        self.targets = targets or TargetRecordRepository()
        self.workers = workers or WorkerRecordRepository()
        self.logs = logs or UploadLogRepository()
        self.access = AccessBusiness()
        self.uploads = UploadBusiness()

    def execute(self, request: SaveUploadRequest) -> SaveUploadResponse:
        user = self.current_user
        self.access.ensure_valid(user)
        file = request.file
        self.uploads.ensure_file(UploadFileFacts(extension=file.extension, size_mb=file.size_mb))
        sheets = WorkbookSheetsBuilder(file).build()
        self.uploads.ensure_sheets(set(sheets))
        parsed = self.uploads.parse(RawWorkbookBuilder(file, sheets).build())
        who = self.access.deleted_by(user)
        changed = (
            self._replace(
                self.production, parsed.production, parsed.production_range, lambda row: row.production_date, who
            ),
            self._replace(self.targets, parsed.targets, parsed.target_range, lambda row: row.target_date, who),
            self._replace(self.workers, parsed.workers, parsed.worker_range, lambda row: row.work_date, who),
        )
        date_range = parsed.production_range
        self.logs.add(
            UploadLog(
                uploaded_at=utc_now(),
                uploaded_by=self.access.saved_by(user),
                file_name=file.filename,
                from_date=date_range.from_date,
                to_date=date_range.to_date,
                saved_rows=len(parsed.production),
                skipped_rows=len(parsed.skipped),
            )
        )
        self.logger.info("Saved %s: rows written production/target/worker = %s", file.filename, changed)
        message = f"Đã lưu {len(parsed.production)} dòng, dữ liệu đến ngày {date_range.to_date:%d/%m/%Y}."
        return SaveUploadResponse(saved_rows=len(parsed.production), to_date=date_range.to_date, message=message)

    def _replace(
        self,
        repository: BaseRepository[TRecord],
        incoming: list[TRecord],
        date_range: DateRange,
        date_of: Callable[[TRecord], date],
        who: str | None,
    ) -> int:
        """The same steps for the 3 tables. Nothing is written when nothing changed."""
        writes = self.uploads.replacement_writes(
            repository.list_all(), repository.list_deleted(), incoming, date_range, date_of, who
        )
        if writes:
            repository.save_many(writes)
        return len(writes)

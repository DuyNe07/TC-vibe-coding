"""Tables filled from the data file, and the upload history."""

from backend.core.base import SqlRepository
from backend.features.sewing_productivity.models.settings_records import UploadLog
from backend.features.sewing_productivity.models.source_records import ProductionRecord, TargetRecord, WorkerRecord


class ProductionRecordRepository(SqlRepository[ProductionRecord]):
    pass


class TargetRecordRepository(SqlRepository[TargetRecord]):
    pass


class WorkerRecordRepository(SqlRepository[WorkerRecord]):
    pass


class UploadLogRepository(SqlRepository[UploadLog]):
    pass

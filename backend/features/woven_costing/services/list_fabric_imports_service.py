"""UC-39 Xem lịch sử cập nhật dữ liệu vải (5 lần gần nhất)."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.constants import IMPORT_LOG_LIMIT
from backend.features.woven_costing.dto.fabric_dto import FabricImportLogDTO, FabricImportLogResponse
from backend.features.woven_costing.repositories.fabric_repository import FabricImportLogRepository


class ListFabricImportsService(BaseService[EmptyRequest, FabricImportLogResponse]):
    def __init__(self, repository: FabricImportLogRepository | None = None) -> None:
        self.repository = repository or FabricImportLogRepository()

    def execute(self, request: EmptyRequest) -> FabricImportLogResponse:
        logs = self.repository.latest(IMPORT_LOG_LIMIT)
        self.logger.info("UC-39 %s import logs", len(logs))
        return FabricImportLogResponse(
            rows=[
                FabricImportLogDTO(
                    imported_at=log.created_at, **log.model_dump(exclude={"id", "created_at", "updated_at"})
                )
                for log in logs
            ]
        )

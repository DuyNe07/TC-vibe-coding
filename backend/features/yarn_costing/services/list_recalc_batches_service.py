"""UC-36 Xem danh sách lần tính lại toàn bộ."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.dto.master_dto import ListRecalcBatchesRequest, RecalcBatchListResponse
from backend.features.yarn_costing.repositories.recalc_batch_repository import RecalcBatchRepository


class ListRecalcBatchesService(BaseService[ListRecalcBatchesRequest, RecalcBatchListResponse]):
    def __init__(self, repository: RecalcBatchRepository | None = None) -> None:
        self.repository = repository or RecalcBatchRepository()

    def execute(self, request: ListRecalcBatchesRequest) -> RecalcBatchListResponse:
        items = [
            b
            for b in self.repository.newest_first()
            if request.factory_code is None or b.factory_code == request.factory_code
        ]
        self.logger.info("Recalculation batches: %s", len(items))
        return RecalcBatchListResponse(items=[batch_dto(b) for b in items])

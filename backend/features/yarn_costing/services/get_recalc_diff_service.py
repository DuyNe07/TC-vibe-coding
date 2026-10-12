"""UC-37 Xem chênh lệch của một lần tính lại."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.builders.file_builders import RecalcDiffFileBuilder
from backend.features.yarn_costing.business.dashboard_business import DashboardBusiness
from backend.features.yarn_costing.dto.master_dto import GetRecalcDiffRequest, RecalcDiffResponse, RecalcDiffRowDTO
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import RecalcBatchRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class GetRecalcDiffService(BaseService[GetRecalcDiffRequest, RecalcDiffResponse]):
    def __init__(self, repository: RecalcBatchRepository | None = None) -> None:
        self.repository = repository or RecalcBatchRepository()
        self.business = DashboardBusiness()

    def execute(self, request: GetRecalcDiffRequest) -> RecalcDiffResponse:
        batch = self.repository.get_by_code(request.batch_id)
        if batch is None:
            raise YarnNotFoundError(f"Không tìm thấy lần tính lại {request.batch_id}.")
        history = PriceHistoryRepository().find(lambda h: h.batch_id == batch.batch_code and h.old is not None)
        names = {y.yarn_code: y.yarn_name for y in YarnRepository().list_all()}
        rows = []
        for h in history:
            if request.line_types and h.line_type not in request.line_types:
                continue
            old, new = h.old.total, h.new.total  # type: ignore[union-attr]
            rows.append(
                RecalcDiffRowDTO(
                    line_code=h.line_code,
                    yarn_name=names.get(h.yarn_code, ""),
                    line_type=h.line_type,
                    old_total=old,
                    new_total=new,
                    diff_vnd=new - old,
                    diff_percent=(new - old) / old * 100 if old else None,
                )
            )
        rows.sort(key=lambda r: r.line_code)
        up, down, average = self.business.batch_changes(batch, history)
        self.logger.info("Recalculation %s: %s changed lines", batch.batch_code, len(rows))
        return RecalcDiffResponse(
            batch=batch_dto(batch),
            items=rows,
            up_count=up,
            down_count=down,
            unchanged_count=max(batch.line_count - len(history), 0),
            avg_percent=average,
            file=RecalcDiffFileBuilder(batch.batch_code, rows).build(),
        )

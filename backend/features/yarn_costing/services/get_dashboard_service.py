"""UC-32 Xem dashboard (BR-53)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.dashboard_business import DashboardBusiness
from backend.features.yarn_costing.dto.dashboard_dto import DashboardResponse, GetDashboardRequest, WeeklyStatDTO
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import RecalcBatchRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

EMPTY_MESSAGE = "Không có dữ liệu trong khoảng ngày đã chọn."


class GetDashboardService(BaseService[GetDashboardRequest, DashboardResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.business = DashboardBusiness()

    def execute(self, request: GetDashboardRequest) -> DashboardResponse:
        date_from, date_to = sorted((request.date_from, request.date_to))
        factory = request.factory_code
        yarns = [y for y in self.repository.list_all() if factory is None or y.factory_code == factory]
        batches = [b for b in RecalcBatchRepository().list_all() if factory is None or b.factory_code == factory]
        last = self.business.last_batch(batches, date_from, date_to)
        history = PriceHistoryRepository().find(lambda h: h.batch_id == last.batch_code) if last else []
        stats = self.business.stats(yarns, batches, history, date_from, date_to)
        has_data = bool(stats.quoted_count or stats.new_request_count or last)
        self.logger.info(
            "Dashboard %s..%s factory=%s: quoted=%s new=%s",
            date_from,
            date_to,
            request.factory_code,
            stats.quoted_count,
            stats.new_request_count,
        )
        return DashboardResponse(
            quoted_count=stats.quoted_count,
            ordered_count=stats.ordered_count,
            ordered_ratio=stats.ordered_ratio,
            new_request_count=stats.new_request_count,
            fulfilment_ratio=stats.fulfilment_ratio,
            waiting_count=stats.waiting_count,
            weekly=[WeeklyStatDTO(**w.model_dump()) for w in stats.weekly],
            status_counts=stats.status_counts,
            last_batch=batch_dto(last) if last else None,
            last_batch_up=stats.last_batch_up,
            last_batch_down=stats.last_batch_down,
            last_batch_avg_percent=stats.last_batch_avg_percent,
            has_data=has_data,
            empty_message="" if has_data else EMPTY_MESSAGE,
        )

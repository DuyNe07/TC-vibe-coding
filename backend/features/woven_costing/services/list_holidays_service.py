"""UC-34 Xem ngày lễ."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.builders.dto_builders import MasterRowsBuilder
from backend.features.woven_costing.dto.master_dto import HolidayListResponse
from backend.features.woven_costing.repositories.master_repository import HolidayRepository


class ListHolidaysService(BaseService[EmptyRequest, HolidayListResponse]):
    def __init__(self, repository: HolidayRepository | None = None) -> None:
        self.repository = repository or HolidayRepository()

    def execute(self, request: EmptyRequest) -> HolidayListResponse:
        holidays = self.repository.list_all()
        self.logger.info("UC-34 %s holidays", len(holidays))
        return HolidayListResponse(rows=MasterRowsBuilder().holidays(holidays))

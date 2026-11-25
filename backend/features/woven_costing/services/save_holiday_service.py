"""UC-11 Quản lý ngày lễ (thêm / xóa bằng cờ xóa, khôi phục được)."""

from backend.core.base import BaseService
from backend.core.exceptions import ConflictError, NotFoundError
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.dto.common_dto import MessageResponse
from backend.features.woven_costing.dto.master_dto import SaveHolidayRequest
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.enums import HolidayAction
from backend.features.woven_costing.models.master import Holiday
from backend.features.woven_costing.repositories.master_repository import HolidayRepository


class SaveHolidayService(BaseService[SaveHolidayRequest, MessageResponse]):
    def __init__(self, repository: HolidayRepository | None = None) -> None:
        self.repository = repository or HolidayRepository()

    def execute(self, request: SaveHolidayRequest) -> MessageResponse:
        AccessBusiness().ensure_use_case(self.current_user, "UC-11")
        day = f"{request.date:%d/%m/%Y}"
        stored = self.repository.by_date(request.date)
        if request.action == HolidayAction.DELETE:
            if stored is None:
                raise NotFoundError(f"Không có ngày lễ {day}.")
            self.repository.delete(stored.id)
            self.logger.info("UC-11 holiday %s deleted (flag)", request.date)
            return MessageResponse(message=f"Đã xóa ngày lễ {day}.")
        if stored is not None:
            raise ConflictError(f"Ngày {day} đã có trong danh sách ngày lễ.")
        if not request.name.strip():
            raise WovenCostingError("Vui lòng nhập tên ngày lễ.")
        deleted = next((h for h in self.repository.list_deleted() if h.date == request.date), None)
        if deleted is not None:
            restored = self.repository.restore(deleted.id)
            self.repository.update(restored.model_copy(update={"name": request.name.strip()}))
        else:
            self.repository.add(Holiday(date=request.date, name=request.name.strip()))
        self.logger.info("UC-11 holiday %s added", request.date)
        return MessageResponse(message=f"Đã thêm ngày lễ {day}: {request.name.strip()}.")

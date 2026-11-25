"""UC-10 Quản lý hệ số theo mã hàng (thêm / sửa / ngừng dùng, không xóa hẳn)."""

from backend.core.base import BaseService
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.dto.common_dto import MessageResponse
from backend.features.woven_costing.dto.master_dto import SaveFabricFactorRequest
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.master import FabricFactor
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.repositories.master_repository import FabricFactorRepository


class SaveFabricFactorService(BaseService[SaveFabricFactorRequest, MessageResponse]):
    def __init__(self, repository: FabricFactorRepository | None = None) -> None:
        self.repository = repository or FabricFactorRepository()

    def execute(self, request: SaveFabricFactorRequest) -> MessageResponse:
        AccessBusiness().ensure_use_case(self.current_user, "UC-10")
        fabric = FabricBusiness()
        code = fabric.ensure_code(request.tcfno)
        fabric.ensure_exists(FabricRepository().by_tcfno(code), code)
        if request.multiplier <= 0:
            raise WovenCostingError("Hệ số nhân phải lớn hơn 0.")
        values = request.model_dump(exclude={"id"}) | {"tcfno": code}
        self.repository.list_with_seed()
        if request.id:
            stored = self.repository.get_or_raise(request.id)
            self.repository.update(stored.model_copy(update=values))
        else:
            self.repository.add(FabricFactor(**values))
        self.logger.info("UC-10 factor %s %s/%s x%s +%s active=%s", code, request.stage, request.cost_item,
                         request.multiplier, request.addition, request.active)  # fmt: skip
        return MessageResponse(message=f"Đã lưu hệ số cho mã {code}.")

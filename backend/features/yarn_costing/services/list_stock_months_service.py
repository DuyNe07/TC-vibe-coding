"""UC-56 (đợt 2): các tháng kho đã lưu."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.dto.material_dto import ListStockMonthsRequest, StockMonthDTO, StockMonthListResponse
from backend.features.yarn_costing.repositories.material_price_repository import StockMonthRepository

USE_CASE = "UC-56"


class ListStockMonthsService(BaseService[ListStockMonthsRequest, StockMonthListResponse]):
    def execute(self, request: ListStockMonthsRequest) -> StockMonthListResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        return StockMonthListResponse(
            items=[
                StockMonthDTO(
                    id=m.id,
                    period=m.period,
                    file_name=m.file_name,
                    material_count=m.material_count,
                    yarn_count=m.yarn_count,
                    accessory_count=m.accessory_count,
                    imported_by=m.imported_by,
                    imported_at=m.created_at,
                )
                for m in StockMonthRepository().ordered()
            ]
        )

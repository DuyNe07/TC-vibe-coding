"""UC-59 Xem bảng giá nguyên liệu bình quân tháng (đợt 2, BR-88, BR-89, BR-92)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import average_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness, previous_period
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.dto.material_dto import GetMaterialAveragesRequest, MaterialAveragesResponse
from backend.features.yarn_costing.repositories.material_price_repository import load_month_inputs

USE_CASE = "UC-59"


class GetMaterialAveragesService(BaseService[GetMaterialAveragesRequest, MaterialAveragesResponse]):
    def execute(self, request: GetMaterialAveragesRequest) -> MaterialAveragesResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        inputs = load_month_inputs(request.period)
        stock = MaterialStockBusiness()
        business = MaterialPriceBusiness()
        rate, monthly, averages, problem = business.month_view(inputs, stock.mapping_key)
        plan_text = " + ".join(
            f"{s.origin.value} {s.percent * 100:.2f}%".replace(".", ",") for s in monthly.cotton_plan
        )
        codes, lots = business.undeclared(
            request.period, inputs.stock_lines, inputs.settings, inputs.lots, inputs.mappings, stock.mapping_key
        )
        return MaterialAveragesResponse(
            period=request.period,
            stock_period=previous_period(request.period),
            exchange_rate=rate,
            plan_text=plan_text,
            problem=problem,
            undeclared_codes=codes,
            undeclared_lots=lots,
            rows=[average_dto(a, rate) for a in averages] if rate else [],
        )

"""UC-64 So đơn giá xuất kho với giá bình quân (đợt 2, BR-89, BR-92, BR-99)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import stock_out_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import (
    MSG_NO_RATE,
    MaterialPriceBusiness,
    month_text,
)
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.dto.material_dto import GetStockOutComparisonRequest, StockOutComparisonResponse
from backend.features.yarn_costing.models.enums import StockSection
from backend.features.yarn_costing.repositories.material_price_repository import (
    QuoteRepository,
    StockLineRepository,
    StockMonthRepository,
    load_month_inputs,
)

USE_CASE = "UC-64"
NO_MONTH = "Chưa có file kho. Vui lòng tải ở thẻ File kho."


class GetStockOutComparisonService(BaseService[GetStockOutComparisonRequest, StockOutComparisonResponse]):
    def execute(self, request: GetStockOutComparisonRequest) -> StockOutComparisonResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        business = MaterialPriceBusiness()
        business.ensure_level(request.gap_percent)
        months = StockMonthRepository().ordered()
        periods = [m.period for m in months]
        if not months:
            return StockOutComparisonResponse(problem=NO_MONTH)
        month = next((m for m in months if m.period == request.period), months[0])
        inputs = load_month_inputs(month.period)  # averages of month M use the stock file of M−1
        rate, _, averages, problem = business.month_view(inputs, MaterialStockBusiness().mapping_key)
        if rate is None:
            return StockOutComparisonResponse(
                period=month.period, months=periods, problem=MSG_NO_RATE.format(month=month_text(month.period))
            )
        rows = business.compare_stock_out(
            month.period,
            StockLineRepository().for_month(month.id),
            inputs.settings,
            inputs.groups,
            averages if not problem else None,
            QuoteRepository().list_all(),
            rate,
            request.gap_percent,
        )
        shown = [r for r in rows if r.is_gap] if request.only_gap else rows
        materials = [stock_out_dto(r) for r in shown if r.section == StockSection.NGUYEN_LIEU]
        yarns = [stock_out_dto(r) for r in shown if r.section == StockSection.SOI_THANH_PHAM]
        return StockOutComparisonResponse(
            period=month.period,
            months=periods,
            exchange_rate=rate,
            material_rows=materials,
            yarn_rows=yarns,
            material_count=sum(1 for r in rows if r.section == StockSection.NGUYEN_LIEU and r.compare_usd is not None),
            yarn_count=sum(1 for r in rows if r.section == StockSection.SOI_THANH_PHAM and r.compare_usd is not None),
            gap_count=sum(1 for r in rows if r.is_gap),
            no_compare_count=sum(1 for r in rows if r.compare_usd is None),
        )

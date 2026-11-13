"""UC-62 (đợt 2): dữ liệu điền sẵn của khối Tính giá - thành phần + tiêu hao (BR-94), nhóm gợi ý (BR-93), mã kế toán
gợi ý (BR-98), hệ số và F&I mặc định của tháng (BR-88)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import group_options
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness
from backend.features.yarn_costing.business.quote_business import QuoteBusiness
from backend.features.yarn_costing.dto.material_dto import (
    AccountingSuggestionDTO,
    CottonShareDTO,
    GetQuoteFormRequest,
    QuoteFormComponentDTO,
    QuoteFormResponse,
)
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.enums import LineType
from backend.features.yarn_costing.repositories.material_price_repository import (
    MaterialPriceGroupRepository,
    MonthlyMaterialSettingRepository,
    QuoteRepository,
    StockLineRepository,
    StockMonthRepository,
    previous_period,
)
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-62"
MSG_NOT_FOUND = "Không tìm thấy dòng giá {code}."


class GetQuoteFormService(BaseService[GetQuoteFormRequest, QuoteFormResponse]):
    def execute(self, request: GetQuoteFormRequest) -> QuoteFormResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        yarns = YarnRepository().list_all()
        yarn = next((y for y in yarns if y.line(request.line_code) is not None), None)
        if yarn is None:
            raise YarnNotFoundError(MSG_NOT_FOUND.format(code=request.line_code))
        business = QuoteBusiness()
        quotes = QuoteRepository().list_all()
        stock_month = StockMonthRepository().current(previous_period(request.period))
        stock_lines = StockLineRepository().for_month(stock_month.id) if stock_month else []
        family = [y for y in yarns if y.factory_code == yarn.factory_code and y.base_code == yarn.base_code]
        suggestions = business.accounting_suggestions(yarn, family, stock_lines)
        line = yarn.line(request.line_code)
        monthly = MaterialPriceBusiness().setting_of(request.period, MonthlyMaterialSettingRepository().list_all())
        return QuoteFormResponse(
            line_code=request.line_code,
            yarn_name=yarn.yarn_name,
            components=[
                QuoteFormComponentDTO(
                    material_label=c.material_label,
                    ratio=c.ratio,
                    loss=business.component_loss(yarn, c),
                    suggested_group_id=business.suggest_group(c.material_label, quotes),
                )
                for c in yarn.components
            ],
            accounting_suggestions=[AccountingSuggestionDTO(code=c, name=n, stock_qty=q) for c, n, q in suggestions],
            default_accounting_code=(line.accounting_code or "") if line else "",
            norm_factor=monthly.norm_factor,
            default_fi=monthly.default_fi,
            group_options=group_options(MaterialPriceGroupRepository().list_all()),
            has_trial_line=any(x.line_type == LineType.THI_NGHIEM and x.total_vnd > 0 for x in yarn.lines),
            supima_percent=business.supima_from_name(yarn.yarn_name),  # BR-112 (bổ sung 2026-11-13)
            cotton_plan=[CottonShareDTO(origin=s.origin, percent=s.percent) for s in monthly.cotton_plan],
        )

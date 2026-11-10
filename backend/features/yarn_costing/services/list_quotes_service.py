"""UC-63 Xem các lần tính giá báo khách (đợt 2)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import quote_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.quote_business import QuoteBusiness
from backend.features.yarn_costing.dto.material_dto import ListQuotesRequest, QuoteListResponse
from backend.features.yarn_costing.repositories.material_price_repository import QuoteRepository

USE_CASE = "UC-63"


class ListQuotesService(BaseService[ListQuotesRequest, QuoteListResponse]):
    def execute(self, request: ListQuotesRequest) -> QuoteListResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        quotes = QuoteRepository().list_all()
        found = QuoteBusiness().filter(
            quotes, request.date_from, request.date_to, request.period, request.customer, request.search
        )
        return QuoteListResponse(
            items=[quote_dto(q) for q in found],
            customers=sorted({q.customer_name for q in quotes if q.customer_name}, key=str.casefold),
            periods=sorted({q.period for q in quotes}, reverse=True),
        )

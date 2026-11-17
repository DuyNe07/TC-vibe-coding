"""UC-63 Xoá một lần tính giá báo khách (đợt 2, BR-97): cờ xoá, chỉ người tính hoặc Phòng SO."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.quote_business import QuoteBusiness
from backend.features.yarn_costing.dto.material_dto import DeleteQuoteRequest, MaterialSaveResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.material_price_repository import QuoteRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-63"
MSG_NOT_FOUND = "Không tìm thấy báo giá."


class DeleteQuoteService(BaseService[DeleteQuoteRequest, MaterialSaveResponse]):
    def execute(self, request: DeleteQuoteRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        repo = QuoteRepository()
        quote = repo.get(request.quote_id)
        if quote is None:
            raise YarnNotFoundError(MSG_NOT_FOUND)
        user = self.current_user
        QuoteBusiness().ensure_can_delete(quote, user.username if user else None, access.is_so(user))
        repo.delete(quote.id)
        AuditLogRepository().add(access.audit_entry(user, USE_CASE, quote.quote_no, f"Xoá báo giá {quote.yarn_name}"))
        return MaterialSaveResponse(message=f"Đã xoá báo giá {quote.quote_no}.", saved_count=1)

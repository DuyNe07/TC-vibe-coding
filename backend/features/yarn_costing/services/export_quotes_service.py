"""UC-63 Xuất Excel các lần tính giá báo khách (đợt 2, 5.12)."""

from backend.core.base import BaseService, FileDownloadDTO, utc_now
from backend.features.yarn_costing.builders.material_dto_builders import quote_dto
from backend.features.yarn_costing.builders.material_file_builders import QuoteExportFileBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.quote_business import QuoteBusiness
from backend.features.yarn_costing.dto.material_dto import ExportQuotesRequest
from backend.features.yarn_costing.repositories.material_price_repository import QuoteRepository

USE_CASE = "UC-63"


class ExportQuotesService(BaseService[ExportQuotesRequest, FileDownloadDTO]):
    def execute(self, request: ExportQuotesRequest) -> FileDownloadDTO:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        found = QuoteBusiness().filter(
            QuoteRepository().list_all(),
            request.date_from,
            request.date_to,
            request.period,
            request.customer,
            request.search,
        )
        self.logger.info("Export %s quotes", len(found))
        return QuoteExportFileBuilder(
            [quote_dto(q) for q in found], f"gia-bao-khach-{utc_now():%Y%m%d-%H%M}.xlsx"
        ).build()

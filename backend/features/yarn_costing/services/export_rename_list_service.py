"""UC-69 Tải danh sách tên nghi sai để sửa bằng Excel (5.13, bổ sung 2026-11-11)."""

from backend.core.base import BaseService, FileDownloadDTO, utc_now
from backend.features.yarn_costing.builders.name_file_builders import RenameListFileBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness
from backend.features.yarn_costing.dto.name_dto import ExportRenameListRequest, SuspectNameDTO
from backend.features.yarn_costing.repositories.name_check_repository import NameWordRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-65"


class ExportRenameListService(BaseService[ExportRenameListRequest, FileDownloadDTO]):
    def execute(self, request: ExportRenameListRequest) -> FileDownloadDTO:
        AccessBusiness().ensure_allowed(self.current_user, USE_CASE)
        business = NameCheckBusiness()
        yarns = YarnRepository().list_all()
        standard, misspellings = NameWordRepository().lookups(business.word_uses(yarns))
        keyword = request.keyword.strip().casefold()
        rows = [
            SuspectNameDTO(**s.model_dump())
            for s in business.suspects(yarns, standard, misspellings)
            if (request.factory_code is None or s.factory_code == request.factory_code)
            and (not request.issues or any(i in request.issues for i in s.issues))
            and (not keyword or keyword in f"{s.yarn_code} {s.yarn_name}".casefold())
        ]
        self.logger.info("Rename list: %s names", len(rows))
        return RenameListFileBuilder(rows, f"sua-ten-soi-{utc_now():%Y%m%d-%H%M}.xlsx").build()

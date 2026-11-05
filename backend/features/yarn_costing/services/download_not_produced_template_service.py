"""UC-48 Tải file mẫu đánh dấu Không sản xuất (5.8, bổ sung 2026-11-05)."""

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.yarn_costing.builders.not_produced_file_builder import NotProducedTemplateBuilder
from backend.features.yarn_costing.dto.import_dto import DownloadNotProducedTemplateRequest


class DownloadNotProducedTemplateService(BaseService[DownloadNotProducedTemplateRequest, FileDownloadDTO]):
    def execute(self, request: DownloadNotProducedTemplateRequest) -> FileDownloadDTO:
        self.logger.info("Not produced template %s", request.factory_code)
        return NotProducedTemplateBuilder(request.factory_code).build()

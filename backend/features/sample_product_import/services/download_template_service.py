"""UC-01: download the Excel import template."""

from backend.core.base import BaseService, EmptyRequest, FileDownloadDTO
from backend.features.sample_product_import.builders.product_builders import ImportTemplateFileBuilder


class DownloadTemplateService(BaseService[EmptyRequest, FileDownloadDTO]):
    def execute(self, request: EmptyRequest) -> FileDownloadDTO:
        self.logger.info("Generating import template")
        return ImportTemplateFileBuilder().build()

"""UC-06 Tải file mẫu bộ định mức."""

from datetime import date

from backend.core.base import BaseService, EmptyRequest, FileDownloadDTO
from backend.features.woven_costing.builders.norm_file_builders import NormSheetsBuilder, NormTemplateBuilder
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository


class DownloadNormTemplateService(BaseService[EmptyRequest, FileDownloadDTO]):
    def __init__(self, repository: NormSetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or NormSetRepository()
        self.today = today or date.today()

    def execute(self, request: EmptyRequest) -> FileDownloadDTO:
        current = self.repository.effective_on(self.today) or self.repository.list_with_seed()[-1]
        book = NormSheetsBuilder(current.tables).build()
        self.logger.info("UC-06 template from norm set %s", current.norm_set_code)
        return NormTemplateBuilder(book, f"bo-dinh-muc-{self.today:%Y%m%d}.xlsx").build()

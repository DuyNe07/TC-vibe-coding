"""UC-37 Kiểm tra bộ định mức (chưa lưu)."""

from backend.core.base import BaseService
from backend.core.exceptions import AppError
from backend.features.woven_costing.builders.norm_file_builders import NormSheetsBuilder, NormWorkbookReaderBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.business.norm_business import NormBusiness
from backend.features.woven_costing.constants import NORM_OPTIONAL_SHEETS
from backend.features.woven_costing.dto.master_dto import (
    NormChangeDTO,
    NormSetPreviewResponse,
    SaveNormSetRequest,
    SheetCountDTO,
)
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository


class PreviewNormSetService(BaseService[SaveNormSetRequest, NormSetPreviewResponse]):
    def __init__(self, repository: NormSetRepository | None = None) -> None:
        self.repository = repository or NormSetRepository()

    def execute(self, request: SaveNormSetRequest) -> NormSetPreviewResponse:
        AccessBusiness().ensure_use_case(self.current_user, "UC-37")
        master = MasterBusiness()
        master.ensure_file(request.file)
        errors: list[str] = []
        sets = self.repository.list_with_seed()
        try:
            master.ensure_unique_date(request.effective_from, [s.effective_from for s in sets])
        except AppError as exc:
            errors.append(exc.message)
        book = NormWorkbookReaderBuilder(request.file).build()
        business = NormBusiness()
        errors += business.validate(book)
        current = self.repository.effective_on(request.effective_from) or sets[-1]
        changes = business.changes(NormSheetsBuilder(current.tables).build(), book) if not errors else []
        self.logger.info("UC-37 %s: %s sheets, %s errors, %s changes", request.file.filename, len(book.sheets),
                         len(errors), len(changes))  # fmt: skip
        return NormSetPreviewResponse(
            sheet_counts=[
                SheetCountDTO(sheet=s.name, rows=len(s.rows)) for s in book.sheets if s.name not in NORM_OPTIONAL_SHEETS
            ],
            optional_sheet_counts=[
                SheetCountDTO(sheet=s.name, rows=len(s.rows)) for s in book.sheets if s.name in NORM_OPTIONAL_SHEETS
            ],
            changes=[NormChangeDTO(**c.model_dump()) for c in changes],
            errors=errors,
        )

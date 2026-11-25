"""UC-08 Xem bộ định mức."""

from datetime import date

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dto_builders import MasterRowsBuilder, NormTablesDtoBuilder
from backend.features.woven_costing.builders.norm_file_builders import NormSheetsBuilder
from backend.features.woven_costing.constants import NORM_OPTIONAL_SHEETS
from backend.features.woven_costing.dto.master_dto import NormSetDetailDTO, NormSetResponse, ViewNormSetRequest
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository


class ViewNormSetService(BaseService[ViewNormSetRequest, NormSetResponse]):
    def __init__(self, repository: NormSetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or NormSetRepository()
        self.today = today or date.today()

    def execute(self, request: ViewNormSetRequest) -> NormSetResponse:
        sets = self.repository.list_with_seed()
        current = self.repository.effective_on(self.today)
        current_code = current.norm_set_code if current else ""
        wanted = request.norm_set_code or current_code or (sets[0].norm_set_code if sets else "")
        selected = next((s for s in sets if s.norm_set_code == wanted), None)
        detail = None
        if selected is not None:
            tables = NormTablesDtoBuilder(NormSheetsBuilder(selected.tables).build()).build()
            detail = NormSetDetailDTO(
                norm_set_code=selected.norm_set_code,
                tables=[t for t in tables if t.sheet not in NORM_OPTIONAL_SHEETS],
                optional_tables=[t for t in tables if t.sheet in NORM_OPTIONAL_SHEETS],
            )
        self.logger.info("UC-08 %s norm sets, showing %s", len(sets), wanted)
        return NormSetResponse(sets=MasterRowsBuilder().norm_sets(sets, current_code), selected=detail)

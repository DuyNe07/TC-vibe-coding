"""UC-07 Kiểm tra và lưu bộ định mức mới."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.norm_file_builders import NormTablesBuilder, NormWorkbookReaderBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.business.norm_business import NormBusiness
from backend.features.woven_costing.constants import SPANDEX_SHEET
from backend.features.woven_costing.dto.master_dto import SaveNormSetRequest, SaveNormSetResponse
from backend.features.woven_costing.exceptions import WovenFileError
from backend.features.woven_costing.models.norm_set import NormSet
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository


class SaveNormSetService(BaseService[SaveNormSetRequest, SaveNormSetResponse]):
    def __init__(self, repository: NormSetRepository | None = None) -> None:
        self.repository = repository or NormSetRepository()

    def execute(self, request: SaveNormSetRequest) -> SaveNormSetResponse:
        access = AccessBusiness()
        access.ensure_use_case(self.current_user, "UC-07")
        master = MasterBusiness()
        master.ensure_file(request.file)
        sets = self.repository.list_with_seed()
        master.ensure_unique_date(request.effective_from, [s.effective_from for s in sets])
        book = NormWorkbookReaderBuilder(request.file).build()
        errors = NormBusiness().validate(book)
        if errors:
            raise WovenFileError(errors[0] if len(errors) == 1 else "File định mức có lỗi:\n" + "\n".join(errors[:20]),
                                 details=errors)  # fmt: skip
        prefix = f"DM-{request.effective_from:%Y%m%d}"
        used = [s.norm_set_code for s in sets if s.norm_set_code.startswith(prefix)]
        code = f"{prefix}-{len(used) + 1:02d}"
        tables = NormTablesBuilder(book).build()
        if book.sheet(SPANDEX_SHEET) is None:  # 4.5.13: a file without sheet Spandex keeps the table in force
            current = self.repository.effective_on(request.effective_from) or sets[-1]
            tables = tables.model_copy(update={"spandex": current.tables.spandex})
        norm_set = NormSet(
            norm_set_code=code,
            effective_from=request.effective_from,
            note=request.note,
            uploaded_by=access.display_name(self.current_user),
            tables=tables,
        )
        self.repository.add(norm_set)
        self.logger.info("UC-07 saved norm set %s effective %s", code, request.effective_from)
        return SaveNormSetResponse(
            norm_set_code=code,
            message=f"Đã lưu bộ định mức {code}, hiệu lực từ {request.effective_from:%d/%m/%Y}.",
        )

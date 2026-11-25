"""UC-01 Kiểm tra dữ liệu vải Peace / WFX (chưa lưu)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.file_readers import FabricFileReaderBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.fabric_import_business import FabricImportBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.constants import MAX_FABRIC_FILES
from backend.features.woven_costing.dto.fabric_dto import (
    FabricImportPreviewResponse,
    FabricImportRowDTO,
    FileCountDTO,
    PreviewFabricImportRequest,
)
from backend.features.woven_costing.exceptions import WovenFileError
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository

WEAVING = "Weaving control"
STANDARD = "TCFNO Standard"


class PreviewFabricImportService(BaseService[PreviewFabricImportRequest, FabricImportPreviewResponse]):
    def __init__(self, repository: FabricRepository | None = None) -> None:
        self.repository = repository or FabricRepository()

    def execute(self, request: PreviewFabricImportRequest) -> FabricImportPreviewResponse:
        AccessBusiness().ensure_use_case(self.current_user, "UC-01")
        if not request.files or len(request.files) > MAX_FABRIC_FILES:
            raise WovenFileError("Hãy chọn 1-4 file Weaving control / TCFNO Standard của Peace hoặc WFX.")
        master = MasterBusiness()
        contents = []
        for file in request.files:
            master.ensure_file(file)
            content = FabricFileReaderBuilder(file).build()
            master.ensure_columns(file.filename, content.missing_columns)
            if content.row_count == 0:
                raise WovenFileError(f"Không đọc được mã vải nào trong file {file.filename}.")
            contents.append(content)
        self.logger.info("UC-01 files read: %s", [(c.file_name, c.system.value, c.row_count) for c in contents])
        outcome = FabricImportBusiness().merge(contents, self.repository.index_by_tcfno(), "")
        self.logger.info(
            "UC-01 result: new=%s changed=%s unchanged=%s missing=%s errors=%s",
            outcome.new_count, outcome.changed_count, outcome.unchanged_count, outcome.missing_yarn_count,
            outcome.error_count,
        )  # fmt: skip
        counts = [
            FileCountDTO(
                file_name=c.file_name,
                kind=f"{c.system.value} - {WEAVING if c.is_weaving else STANDARD}",
                count=c.row_count,
            )
            for c in contents
        ]
        return FabricImportPreviewResponse(
            file_names=[c.file_name for c in contents],
            file_counts=counts,
            new_count=outcome.new_count,
            changed_count=outcome.changed_count,
            unchanged_count=outcome.unchanged_count,
            missing_yarn_count=outcome.missing_yarn_count,
            error_count=outcome.error_count,
            rows=[FabricImportRowDTO(**row.model_dump()) for row in outcome.rows],
        )

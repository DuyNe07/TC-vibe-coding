"""UC-02 Lưu dữ liệu vải."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.file_readers import FabricFileReaderBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.fabric_import_business import FabricImportBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.constants import MAX_FABRIC_FILES
from backend.features.woven_costing.dto.fabric_dto import FabricImportSaveResponse, PreviewFabricImportRequest
from backend.features.woven_costing.exceptions import WovenFileError
from backend.features.woven_costing.models.fabric import FabricImportLog
from backend.features.woven_costing.repositories.fabric_repository import FabricImportLogRepository, FabricRepository


class SaveFabricImportService(BaseService[PreviewFabricImportRequest, FabricImportSaveResponse]):
    def __init__(
        self, repository: FabricRepository | None = None, logs: FabricImportLogRepository | None = None
    ) -> None:
        self.repository = repository or FabricRepository()
        self.logs = logs or FabricImportLogRepository()

    def execute(self, request: PreviewFabricImportRequest) -> FabricImportSaveResponse:
        access = AccessBusiness()
        access.ensure_use_case(self.current_user, "UC-02")
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
        user = access.display_name(self.current_user)
        outcome = FabricImportBusiness().merge(contents, self.repository.index_by_tcfno(), user)
        self.repository.save_many(outcome.to_save)
        self.logs.add(
            FabricImportLog(
                imported_by=user,
                file_names="; ".join(c.file_name for c in contents),
                new_count=outcome.new_count,
                changed_count=outcome.changed_count,
                unchanged_count=outcome.unchanged_count,
                missing_yarn_count=outcome.missing_yarn_count,
                error_count=outcome.error_count,
            )
        )
        self.logger.info(
            "UC-02 saved %s fabrics (new=%s, changed=%s)",
            len(outcome.to_save),
            outcome.new_count,
            outcome.changed_count,
        )
        message = (
            f"Đã lưu: {outcome.new_count} mã mới, {outcome.changed_count} mã cập nhật. "
            f"{outcome.missing_yarn_count} mã thiếu sợi cần kiểm tra."
        )
        return FabricImportSaveResponse(
            new_count=outcome.new_count,
            changed_count=outcome.changed_count,
            missing_yarn_count=outcome.missing_yarn_count,
            message=message,
        )

"""UC-60 Nhập file hàng sắp về (đợt 2; 5.11, BR-90, BR-91)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_file_builders import ArrivalFileReaderBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO
from backend.features.yarn_costing.dto.material_dto import ArrivalImportResponse, ImportArrivalFileRequest
from backend.features.yarn_costing.exceptions import ImportFileError, YarnValidationError
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.models.material_price import ArrivalImport
from backend.features.yarn_costing.repositories.material_price_repository import (
    ArrivalImportRepository,
    ArrivalLotRepository,
    ArrivalMappingRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-60"
MSG_NO_VALID = "Không có dòng hợp lệ để lưu."


class ImportArrivalFileService(BaseService[ImportArrivalFileRequest, ArrivalImportResponse]):
    def execute(self, request: ImportArrivalFileRequest) -> ArrivalImportResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        file = request.file
        ImportBusiness().ensure_file_valid(  # BR-41
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        parsed = ArrivalFileReaderBuilder(file).build()
        if parsed.problem:
            raise ImportFileError(parsed.problem)
        business = MaterialStockBusiness()
        record = ArrivalImport(file_name=file.filename, sheet_name=parsed.sheet)
        lots, rejected = business.read_arrival_rows(parsed.rows, record.id)
        lot_repo = ArrivalLotRepository()
        current = lot_repo.list_all()
        mapping_repo = ArrivalMappingRepository()
        new_pairs = business.new_mappings(lots, mapping_repo.by_key())
        response = ArrivalImportResponse(
            message="",
            sheet=parsed.sheet,
            valid_count=len(lots),
            s1_count=sum(1 for lot in lots if lot.factory_code == FactoryCode.S1),
            s4_count=sum(1 for lot in lots if lot.factory_code == FactoryCode.S4),
            replace_count=len(current),
            new_pairs=len(new_pairs),
            rejected_rows=[RejectedRowDTO(sheet=parsed.sheet, excel_row=r, key=c, reason=m) for r, c, m in rejected],
        )
        self.logger.info("Arrival file %s: %s lots, %s rejected", file.filename, len(lots), len(rejected))
        if not request.commit:
            return response.model_copy(
                update={
                    "message": (
                        f"Kiểm tra file {file.filename} (sheet {parsed.sheet}): {len(lots)} lô hợp lệ, bị loại "
                        f"{len(rejected)} dòng. Lưu sẽ thay toàn bộ {len(current)} lô hiện có (kể cả lô nhập tay)."
                    )
                }
            )
        if not lots:
            raise YarnValidationError(MSG_NO_VALID)
        # BR-91: the file is the source - every current lot is flagged deleted, in ONE write (sửa 2026-11-13: trước đây
        # từng lô một, mỗi lô một lần đọc lại cả bảng → lưu mất 40-50 giây trên cơ sở dữ liệu dùng chung)
        lot_repo.clear()
        label = access.user_label(self.current_user)
        ArrivalImportRepository().add(
            record.model_copy(update={"lot_count": len(lots), "rejected_count": len(rejected), "imported_by": label})
        )
        lot_repo.save_many([lot.model_copy(update={"created_by": label, "updated_by": label}) for lot in lots])
        mapping_repo.save_many(new_pairs)
        AuditLogRepository().add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                "Hàng sắp về",
                f"{file.filename} / {parsed.sheet}: {len(current)} → {len(lots)} lô; {len(new_pairs)} cặp mới",
            )
        )
        return response.model_copy(
            update={
                "committed": True,
                "message": (
                    f"Đã lưu {len(lots)} lô hàng sắp về (thay {len(current)} lô cũ); {len(new_pairs)} cặp nhà cung cấp "
                    "+ mô tả mới cần khai báo nhóm."
                ),
            }
        )

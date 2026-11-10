"""UC-56 Tải file kho tháng (đợt 2; 5.10, BR-86, BR-87)."""

import re

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_file_builders import StockFileReaderBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.material_price_business import month_text
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO
from backend.features.yarn_costing.dto.material_dto import ImportStockFileRequest, StockImportResponse
from backend.features.yarn_costing.exceptions import ImportFileError, YarnValidationError
from backend.features.yarn_costing.models.enums import StockSection
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.models.material_price import StockMonth
from backend.features.yarn_costing.repositories.material_price_repository import (
    StockItemSettingRepository,
    StockLineRepository,
    StockMonthRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-56"
PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MSG_PICK_MONTH = "Vui lòng chọn tháng của file."
MSG_NO_VALID = "Không có dòng hợp lệ để lưu."


class ImportStockFileService(BaseService[ImportStockFileRequest, StockImportResponse]):
    def execute(self, request: ImportStockFileRequest) -> StockImportResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        file = request.file
        ImportBusiness().ensure_file_valid(  # BR-41
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        parsed = StockFileReaderBuilder(file).build()
        if parsed.problem:
            raise ImportFileError(parsed.problem)
        business = MaterialStockBusiness()
        period_read = business.period_of(parsed.period_text)
        period = request.period.strip() or period_read
        if (request.commit or period) and not PERIOD.match(period):  # preview without a month: Sales picks it on screen
            raise YarnValidationError(MSG_PICK_MONTH)
        month = StockMonth(period=period, file_name=file.filename)
        lines, rejected = business.read_stock_rows(parsed.rows, month.id, period)
        counts = {section: sum(1 for line in lines if line.section == section) for section in StockSection}
        settings_repo = StockItemSettingRepository()
        settings, new_codes = business.merge_settings(lines, settings_repo.by_code())
        months = StockMonthRepository()
        old = months.current(period)
        replace_note = (
            f"Tháng này đã có bản lưu ngày {old.created_at:%d/%m/%Y} của {old.imported_by}, lưu sẽ thay bản đó."
            if old
            else ""
        )
        rejected_rows = [RejectedRowDTO(sheet="", excel_row=r, key=c, reason=m) for r, c, m in rejected]
        response = StockImportResponse(
            message="",
            period=period,
            period_read=period_read,
            material_count=counts[StockSection.NGUYEN_LIEU],
            yarn_count=counts[StockSection.SOI_THANH_PHAM],
            accessory_count=counts[StockSection.PHU_LIEU],
            new_codes=new_codes,
            replace_note=replace_note,
            rejected_rows=rejected_rows,
        )
        self.logger.info(
            "Stock file %s month %s: %s rows, %s rejected", file.filename, period, len(lines), len(rejected)
        )
        if not request.commit:
            return response.model_copy(
                update={
                    "message": (
                        f"Kiểm tra file {file.filename}: tháng {month_text(period) if period else 'chưa rõ'}, "
                        f"{len(lines)} mã hợp lệ, "
                        f"bị loại {len(rejected)} dòng, {new_codes} mã nguyên liệu mới cần khai báo."
                    )
                }
            )
        if not lines:
            raise YarnValidationError(MSG_NO_VALID)
        line_repo = StockLineRepository()
        old_count = 0
        if old is not None:  # BR-87: the previous version is flagged deleted, never removed
            old_lines = line_repo.for_month(old.id)
            old_count = len(old_lines)
            for line in old_lines:
                line_repo.delete(line.id)
            months.delete(old.id)
        label = access.user_label(self.current_user)
        months.add(
            month.model_copy(
                update={
                    "imported_by": label,
                    "material_count": response.material_count,
                    "yarn_count": response.yarn_count,
                    "accessory_count": response.accessory_count,
                }
            )
        )
        line_repo.save_many(lines)
        settings_repo.save_many(settings)
        AuditLogRepository().add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                f"Kho {period}",
                f"{file.filename}: {old_count} → {len(lines)} mã; {new_codes} mã mới",
            )
        )
        return response.model_copy(
            update={
                "committed": True,
                "message": (
                    f"Đã lưu file kho tháng {month_text(period)}: {response.material_count} mã nguyên liệu, "
                    f"{response.yarn_count} mã sợi thành phẩm, {response.accessory_count} mã phụ liệu; "
                    f"{new_codes} mã nguyên liệu mới cần khai báo."
                ),
            }
        )

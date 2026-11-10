"""UC-53 Tải file giá thành kế toán - file Z (5.9, BR-80, BR-81; bổ sung 2026-11-10)."""

from decimal import Decimal

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.accounting_file_builder import AccountingFileReaderBuilder
from backend.features.yarn_costing.builders.file_builders import ImportResultFileBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.accounting_cost_business import AccountingCostBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO, SheetResultDTO
from backend.features.yarn_costing.dto.sales_dto import (
    AccountingImportResponse,
    AccountingMonthCheckDTO,
    ImportAccountingFileRequest,
)
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.accounting_cost import AccountingCostLine, AccountingCostMonth
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.repositories.accounting_cost_repository import (
    AccountingCostLineRepository,
    AccountingCostMonthRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-53"
MSG_NO_VALID = "Không có dòng hợp lệ để lưu."


def month_label(period: str) -> str:
    year, month = period.split("-")
    return f"{month}/{year}"


class ImportAccountingFileService(BaseService[ImportAccountingFileRequest, AccountingImportResponse]):
    def __init__(
        self,
        months: AccountingCostMonthRepository | None = None,
        lines: AccountingCostLineRepository | None = None,
    ) -> None:
        self.months = months or AccountingCostMonthRepository()
        self.lines = lines or AccountingCostLineRepository()
        self.access = AccessBusiness()
        self.business = AccountingCostBusiness()

    def execute(self, request: ImportAccountingFileRequest) -> AccountingImportResponse:
        file = request.file
        self.access.ensure_allowed(self.current_user, USE_CASE)
        ImportBusiness().ensure_file_valid(  # BR-41
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        sheets = AccountingFileReaderBuilder(file, self.business.sheet_period).build()
        checks: list[AccountingMonthCheckDTO] = []
        rejected_rows: list[RejectedRowDTO] = []
        ready: list[tuple[AccountingCostMonth, list[AccountingCostLine], AccountingCostMonth | None, str]] = []
        for sheet in sheets:
            if sheet.problem:
                checks.append(AccountingMonthCheckDTO(period=sheet.period, sheet=sheet.sheet, note=sheet.problem))
                continue
            month = AccountingCostMonth(period=sheet.period, file_name=file.filename, sheet_name=sheet.sheet)
            valid, rejected = self.business.read_rows(sheet.rows, month.id, sheet.period)
            rejected_rows += [RejectedRowDTO(sheet=sheet.sheet, excel_row=r, key=c, reason=m) for r, c, m in rejected]
            old = self.months.current(sheet.period)
            note = (
                f"Tháng này đã có bản lưu ngày {old.created_at:%d/%m/%Y} của {old.imported_by}, lưu sẽ thay bản đó."
                if old
                else ""
            )
            quantity = sum((line.quantity for line in valid), Decimal(0))
            checks.append(
                AccountingMonthCheckDTO(
                    period=sheet.period,
                    sheet=sheet.sheet,
                    s1_count=sum(1 for line in valid if line.factory_code.value == "S1"),
                    s4_count=sum(1 for line in valid if line.factory_code.value == "S4"),
                    total_quantity=quantity,
                    rejected_count=len(rejected),
                    note=note,
                )
            )
            if valid:
                month = month.model_copy(update={"row_count": len(valid), "total_quantity": quantity})
                ready.append((month, valid, old, sheet.sheet))
        valid_count = sum(len(lines) for _, lines, _, _ in ready)
        self.logger.info(
            "File Z %s: %s month sheets, %s valid rows, %s rejected",
            file.filename,
            len(ready),
            valid_count,
            len(rejected_rows),
        )
        if not request.commit:
            return AccountingImportResponse(
                message=(
                    f"Kiểm tra file {file.filename}: {len(ready)} tháng, {valid_count} mã hợp lệ, "
                    f"bị loại {len(rejected_rows)} dòng. Bấm 'Lưu {len(ready)} tháng' để lưu."
                ),
                valid_count=valid_count,
                months=checks,
                rejected_rows=rejected_rows,
            )
        if not ready:
            raise YarnValidationError(MSG_NO_VALID)
        label = self.access.user_label(self.current_user)
        audit = AuditLogRepository()
        for month, lines, old, sheet_name in ready:
            old_count = 0
            if old is not None:  # BR-81: the previous version is flagged deleted, never removed
                old_lines = self.lines.for_month(old.id)
                old_count = len(old_lines)
                for line in old_lines:
                    self.lines.delete(line.id)
                self.months.delete(old.id)
            self.months.add(month.model_copy(update={"imported_by": label}))
            self.lines.save_many(lines)
            audit.add(
                self.access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    f"Z {month.period}",
                    f"{file.filename} / {sheet_name}: {old_count} → {len(lines)} mã",
                )
            )
        periods = ", ".join(month_label(m.period) for m, _, _, _ in ready)
        sheet_results = [
            SheetResultDTO(
                sheet=c.sheet,
                read=c.s1_count + c.s4_count + c.rejected_count,
                created=c.s1_count + c.s4_count,
                rejected=c.rejected_count,
            )
            for c in checks
        ]
        self.logger.info("File Z %s saved: months %s, %s rows", file.filename, periods, valid_count)
        return AccountingImportResponse(
            message=(f"Đã lưu giá thành kế toán tháng {periods}: {valid_count} mã, bị loại {len(rejected_rows)} dòng."),
            committed=True,
            valid_count=valid_count,
            months=checks,
            rejected_rows=rejected_rows,
            result_file=ImportResultFileBuilder(f"Z-{ready[0][0].period}", sheet_results, rejected_rows).build(),
        )

"""UC-48 Đánh dấu Không sản xuất hàng loạt bằng file (5.8, BR-72, BR-75; bổ sung 2026-11-05)."""

from datetime import date

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.file_builders import ImportResultFileBuilder
from backend.features.yarn_costing.builders.not_produced_file_builder import (
    NP_SHEET,
    NotProducedFileReaderBuilder,
)
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.not_produced_business import NotProducedBusiness
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from backend.features.yarn_costing.dto.import_dto import (
    ImportNotProducedFileRequest,
    NotProducedImportResponse,
    NotProducedRowDTO,
    RejectedRowDTO,
    SheetResultDTO,
)
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import ImportMode
from backend.features.yarn_costing.models.legacy_price import ImportBatch, SheetCount
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.repositories.legacy_price_repository import ImportBatchRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-48"
MSG_NO_VALID = "Không có mã hợp lệ để lưu."


class ImportNotProducedFileService(BaseService[ImportNotProducedFileRequest, NotProducedImportResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.business = NotProducedBusiness()
        self.importer = ImportBusiness()
        self.requests = RequestBusiness()

    def execute(self, request: ImportNotProducedFileRequest) -> NotProducedImportResponse:
        factory, file = request.factory_code, request.file
        self.access.ensure_allowed(self.current_user, USE_CASE, factory.value)
        self.importer.ensure_file_valid(  # BR-41
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        rows = NotProducedFileReaderBuilder(file).build()
        yarns = self.repository.list_all()
        valid, rejected, skipped = self.business.plan_file(
            rows, factory, yarns, lambda raw: self.requests.normalize_import_code(raw)[0]
        )
        valid_rows = [
            NotProducedRowDTO(
                excel_row=excel_row,
                yarn_code=family[0].yarn_code,
                yarn_name=family[0].yarn_name,
                status=family[0].status.value,
                version_count=len(family),
                line_count=sum(len(y.lines) for y in family),
                reason=reason,
            )
            for excel_row, family, reason in valid
        ]
        problem_rows = [RejectedRowDTO(sheet=NP_SHEET, excel_row=r, key=c, reason=m) for r, c, m in rejected]
        problem_rows += [
            RejectedRowDTO(sheet=NP_SHEET, excel_row=r, key=c, reason=f"Bỏ qua: {m}") for r, c, m in skipped
        ]
        summary = dict(
            valid_count=len(valid_rows),
            revision_count=sum(r.version_count - 1 for r in valid_rows),
            line_count=sum(r.line_count for r in valid_rows),
            rejected_count=len(rejected),
            skipped_count=len(skipped),
            valid_rows=valid_rows,
            rejected_rows=problem_rows,
        )
        self.logger.info(
            "Not produced file %s (%s): %s rows, %s valid, %s rejected, %s skipped",
            file.filename,
            factory,
            len(rows),
            len(valid),
            len(rejected),
            len(skipped),
        )
        if not request.commit:
            return NotProducedImportResponse(
                message=(
                    f"Kiểm tra file {file.filename}: {len(valid)} mã hợp lệ (gỡ {summary['line_count']} dòng giá), "
                    f"bị loại {len(rejected)} dòng, bỏ qua {len(skipped)} dòng. Bấm 'Lưu {len(valid)} mã hợp lệ' để lưu."
                ),
                **summary,
            )
        if not valid:
            raise YarnValidationError(MSG_NO_VALID)
        label = self.access.user_label(self.current_user)
        now = utc_now()
        changed, history = [], []
        removed = 0
        for _, family, reason in valid:
            updated, entries, count = self.business.mark(family, reason, label, now)
            changed += updated
            history += entries
            removed += count
        self.repository.store(yarns, changed)
        PriceHistoryRepository().add_many(history)
        import_repo = ImportBatchRepository()
        prefix = f"NF-{factory.value}-"
        numbers = [
            int(b.batch_code[len(prefix) :])
            for b in import_repo.list_all()
            if b.batch_code.startswith(prefix) and b.batch_code[len(prefix) :].isdigit()
        ]
        import_id = f"{prefix}{max(numbers, default=0) + 1:03d}"
        sheet = SheetResultDTO(sheet=NP_SHEET, read=len(rows), updated=len(valid), rejected=len(rejected))
        import_repo.add(
            ImportBatch(
                batch_code=import_id,
                factory_code=factory,
                mode=ImportMode.KHONG_SAN_XUAT,
                cutoff_date=date.today(),
                file_name=file.filename,
                imported_by=label,
                sheets=[SheetCount(**sheet.model_dump())],
            )
        )
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                USE_CASE,
                f"{factory.value} / {import_id}",
                f"{file.filename}: {len(valid)} mã → Không sản xuất ({', '.join(r.yarn_code for r in valid_rows[:20])}"
                f"{'...' if len(valid_rows) > 20 else ''}), gỡ {removed} dòng giá, bị loại {len(rejected)} dòng",
                "Theo lý do từng dòng trong file",
            )
        )
        self.logger.info("Not produced file %s committed: %s yarns, %s lines removed", import_id, len(changed), removed)
        return NotProducedImportResponse(
            message=(
                f"Đã đánh dấu Không sản xuất cho {len(valid)} mã (gỡ {removed} dòng giá), bị loại {len(rejected)} dòng."
            ),
            committed=True,
            import_id=import_id,
            result_file=ImportResultFileBuilder(import_id, [sheet], problem_rows).build(),
            **{**summary, "line_count": removed},
        )

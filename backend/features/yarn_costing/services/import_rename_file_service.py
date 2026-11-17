"""UC-69 Đổi tên hàng loạt bằng file (5.13, bổ sung 2026-11-11; BR-105 từng dòng)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.name_file_builders import RENAME_SHEET, RenameFileReaderBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness, upper_name
from backend.features.yarn_costing.constants import ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from backend.features.yarn_costing.dto.import_dto import RejectedRowDTO
from backend.features.yarn_costing.dto.name_dto import ImportRenameFileRequest, RenameImportResponse, RenameRowDTO
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.name_check_repository import NameWordRepository, PendingWordRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-69"
MSG_NOT_FOUND = "Không có mã '{code}' ở xưởng {factory}."
MSG_DUP = "Tên mới '{name}' bị trùng trong file."
MSG_NO_VALID = "Không có dòng hợp lệ để lưu."


class ImportRenameFileService(BaseService[ImportRenameFileRequest, RenameImportResponse]):
    def execute(self, request: ImportRenameFileRequest) -> RenameImportResponse:
        access = AccessBusiness()
        access.ensure_allowed(self.current_user, USE_CASE)
        file = request.file
        ImportBusiness().ensure_file_valid(  # BR-41
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        rows = RenameFileReaderBuilder(file).build()
        business = NameCheckBusiness()
        repo, groups_repo = YarnRepository(), LossGroupRepository()
        yarns = {y.id: y for y in repo.list_all()}
        groups = {g.id: g for g in groups_repo.list_all()}
        standard, misspellings = NameWordRepository().lookups(business.word_uses(list(yarns.values())))
        label = access.user_label(self.current_user)
        is_so = access.is_so(self.current_user)
        counts: dict[tuple[str, str], int] = {}
        for _, cells in rows:
            key = (str(cells.get("factory") or "").strip().upper(), upper_name(str(cells.get("new_name") or "")))
            counts[key] = counts.get(key, 0) + 1
        valid: list[RenameRowDTO] = []
        rejected: list[RejectedRowDTO] = []
        changed_yarns, changed_groups, pending = {}, {}, []
        now = utc_now()
        for excel_row, cells in rows:
            factory = str(cells.get("factory") or "").strip().upper()
            code = str(cells.get("code") or "").strip()
            new_name = str(cells.get("new_name") or "")
            reason = str(cells.get("reason") or "")
            try:
                if counts[(factory, upper_name(new_name))] > 1:
                    raise YarnValidationError(MSG_DUP.format(name=upper_name(new_name)))
                current = list(yarns.values())
                base = next(
                    (y for y in current if y.factory_code.value == factory and y.yarn_code == code and y.is_base), None
                )
                if base is None:
                    raise YarnValidationError(MSG_NOT_FOUND.format(code=code, factory=factory or "-"))
                access.ensure_allowed(self.current_user, USE_CASE, factory)
                family = [y for y in current if y.factory_code == base.factory_code and y.base_code == base.base_code]
                changed, group_changes, old_key, new_key, check = business.plan_rename(
                    base,
                    family,
                    new_name,
                    reason,
                    reason,
                    is_so,
                    current,
                    list(groups.values()),
                    standard,
                    misspellings,
                    label,
                    now,
                )
            except YarnValidationError as exc:
                rejected.append(RejectedRowDTO(sheet=RENAME_SHEET, excel_row=excel_row, key=code, reason=exc.message))
                continue
            for y in changed:  # later rows see the earlier renames of the same file
                yarns[y.id] = changed_yarns[y.id] = y
            for g in group_changes:
                groups[g.id] = changed_groups[g.id] = g
            if check.unknown:
                pending.append(([u.word for u in check.unknown], base.yarn_code, reason.strip()))
            valid.append(
                RenameRowDTO(
                    factory_code=base.factory_code,
                    yarn_code=base.yarn_code,
                    old_name=base.yarn_name,
                    new_name=check.name,
                    reason=reason.strip(),
                    old_loss_group=old_key,
                    new_loss_group=new_key,
                )
            )
        self.logger.info("Rename file %s: %s valid, %s rejected", file.filename, len(valid), len(rejected))
        if not request.commit:
            return RenameImportResponse(
                message=f"Kiểm tra file {file.filename}: {len(valid)} tên hợp lệ, bị loại {len(rejected)} dòng.",
                valid=valid,
                rejected_rows=rejected,
            )
        if not valid:
            raise YarnValidationError(MSG_NO_VALID)
        repo.save_many(list(changed_yarns.values()))
        groups_repo.save_many(list(changed_groups.values()))
        words = PendingWordRepository()
        for found, code, reason in pending:
            words.record(found, code, label, reason)
        AuditLogRepository().add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                file.filename,
                "; ".join(f"{r.yarn_code}: '{r.old_name}' → '{r.new_name}'" for r in valid),
            )
        )
        return RenameImportResponse(
            message=f"Đã đổi tên {len(valid)} sợi, bị loại {len(rejected)} dòng.",
            committed=True,
            valid=valid,
            rejected_rows=rejected,
        )

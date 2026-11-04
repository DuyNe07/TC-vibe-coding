"""UC-45 Kiểm tra và lưu file khai báo thành phần sợi pha (BR-66..BR-69; tính lại theo BR-36 / BR-24)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.component_file_builder import ComponentFileReaderBuilder
from backend.features.yarn_costing.builders.file_builders import ImportResultFileBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.component_import_business import ComponentImportBusiness
from backend.features.yarn_costing.business.display_business import format_percent
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.constants import (
    ALLOWED_EXTENSIONS,
    COMP_SHEET,
    MAX_SHEET_ROWS,
    MAX_UPLOAD_MB,
    MSG_COMP_NO_VALID,
)
from backend.features.yarn_costing.dto.import_dto import (
    ComponentGroupResultDTO,
    ComponentImportResponse,
    ImportComponentFileRequest,
    RejectedRowDTO,
    SheetResultDTO,
    UnmatchedYarnDTO,
)
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import ImportMode, PriceEvent, YarnStatus
from backend.features.yarn_costing.models.legacy_price import ImportBatch, SheetCount
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.legacy_price_repository import ImportBatchRepository
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

UNMATCHED_SHEET = "Mã sợi"


def _components_text(components: list) -> str:
    return "; ".join(f"{c.component_group_key} {format_percent(c.ratio)}%" for c in components)


class ImportComponentFileService(BaseService[ImportComponentFileRequest, ComponentImportResponse]):
    def __init__(self, repository: LossGroupRepository | None = None) -> None:
        self.repository = repository or LossGroupRepository()
        self.access = AccessBusiness()
        self.business = ComponentImportBusiness()
        self.importer = ImportBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: ImportComponentFileRequest) -> ComponentImportResponse:
        factory, file = request.factory_code, request.file
        self.access.ensure_allowed(self.current_user, "UC-45", factory.value)
        self.importer.ensure_file_valid(  # BR-41
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        rows = ComponentFileReaderBuilder(file).build()
        self.importer.ensure_file_valid(FileCheck(extension_ok=True, size_ok=True, rows_ok=len(rows) <= MAX_SHEET_ROWS))
        data = load_factory_data(factory)
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        label = self.access.user_label(self.current_user)
        now = utc_now()
        plan = self.business.plan(
            rows, factory, data.loss_groups, data.stages, yarns, self.access.is_so(self.current_user), label, now
        )
        self.logger.info(
            "Component file %s (%s): %s rows, %s groups valid, %s rejected, %s yarns affected, %s unmatched",
            file.filename,
            factory,
            len(rows),
            len(plan.changes),
            len(plan.rejected_rows),
            plan.affected_yarn_count,
            len(plan.unmatched),
        )
        stage_codes = [s.stage_code for s in sorted(data.stages, key=lambda s: s.sequence) if not s.is_packaging]
        groups_dto = [
            ComponentGroupResultDTO(
                excel_row=c.excel_row,
                group_key=c.group.group_key,
                created=c.created,
                old_level=c.old_level,
                new_level=c.group.level.value,
                components_text=_components_text(c.group.components),
                old_losses=c.old_losses,
                new_losses=dict(c.group.losses),
                affected_count=c.affected_count,
            )
            for c in plan.changes
        ]
        rejected = [RejectedRowDTO(**r.model_dump()) for r in plan.rejected_rows]
        unmatched = [UnmatchedYarnDTO(**u.model_dump()) for u in plan.unmatched]
        created = sum(1 for c in plan.changes if c.created)
        summary = dict(
            valid_count=len(plan.changes),
            created_count=created,
            rejected_count=len(rejected),
            affected_count=plan.affected_yarn_count,
            unmatched_count=len({u.yarn_code for u in unmatched}),
            groups=groups_dto,
            rejected_rows=rejected,
            unmatched=unmatched,
            stage_codes=stage_codes,
        )
        if not request.commit:
            return ComponentImportResponse(
                message=(
                    f"Kiểm tra file {file.filename}: {len(plan.changes)} nhóm hợp lệ (tạo mới {created}), bị loại "
                    f"{len(rejected)} dòng, {plan.affected_yarn_count} mã bị ảnh hưởng. "
                    f"Bấm 'Lưu {len(plan.changes)} nhóm hợp lệ' để lưu."
                ),
                **summary,
            )
        self.master.require_date_and_reason(request.effective_date, request.reason)
        if not plan.changes:
            raise YarnValidationError(MSG_COMP_NO_VALID)
        saved = [c.group for c in plan.changes] + plan.recomputed
        self.repository.save_many(saved)
        by_key = {**data.loss_groups, **{g.group_key: g for g in saved}}
        data = data.model_copy(update={"loss_groups": by_key})
        relabeled = {y.id: y for y in plan.relabeled_yarns}
        merged = [relabeled.get(y.id, y) for y in yarns]
        unmatched_codes = {u.yarn_code for u in plan.unmatched}
        affected = set(plan.affected_keys)
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        outcome = self.recalc.recalculate(
            merged,
            data,
            PriceEvent.SUA_TIEU_HAO,
            now,
            request.effective_date,  # type: ignore[arg-type]
            selector=lambda y: y.loss_group_key in affected and y.yarn_code not in unmatched_codes,
            changed_by=label,
            batch_id=self.recalc.batch_code(factory.value, codes),
            reason=request.reason,
        )
        changed = dict(relabeled)
        changed.update({y.id: y for y in outcome.yarns})
        for yarn in merged:  # BR-68: components that could not be matched → "Chưa tính được", price kept
            if yarn.yarn_code in unmatched_codes and self.recalc.is_recalculable(yarn):
                reasons = [self.business.unmatched_message(u) for u in plan.unmatched if u.yarn_code == yarn.yarn_code]
                changed[yarn.id] = yarn.model_copy(
                    update={"status": YarnStatus.CHUA_TINH_DUOC, "status_reasons": reasons}
                )
        yarn_repo.store(yarns, list(changed.values()))
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.SUA_TIEU_HAO, request.effective_date, request.reason, label, outcome, codes
        )  # type: ignore[arg-type]
        batch_repo.add(batch)
        import_repo = ImportBatchRepository()
        prefix = f"NF-{factory.value}-"
        numbers = [
            int(b.batch_code[len(prefix) :])
            for b in import_repo.list_all()
            if b.batch_code.startswith(prefix) and b.batch_code[len(prefix) :].isdigit()
        ]
        import_id = f"{prefix}{max(numbers, default=0) + 1:03d}"
        sheet = SheetResultDTO(
            sheet=COMP_SHEET,
            read=len(rows),
            created=created,
            updated=len(plan.changes) - created,
            rejected=len(rejected),
        )
        import_repo.add(
            ImportBatch(
                batch_code=import_id,
                factory_code=factory,
                mode=ImportMode.THANH_PHAN,
                cutoff_date=request.effective_date,  # type: ignore[arg-type]
                file_name=file.filename,
                imported_by=label,
                sheets=[SheetCount(**sheet.model_dump())],
            )
        )
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                "UC-45",
                f"{factory.value} / {import_id}",
                f"{file.filename}: {len(plan.changes)} nhóm (tạo mới {created}), bị loại {len(rejected)} dòng; "
                f"lần tính lại {batch.batch_code}",
                request.reason,
            )
        )
        result_rows = rejected + [
            RejectedRowDTO(
                sheet=UNMATCHED_SHEET, excel_row=0, key=u.yarn_code, reason=self.business.unmatched_message(u)
            )
            for u in plan.unmatched
        ]
        priced_failed = outcome.failed_yarn_count + len(unmatched_codes)
        self.logger.info(
            "Component file %s committed: %s groups saved, %s yarns recalculated, batch %s",
            import_id,
            len(saved),
            outcome.yarn_count,
            batch.batch_code,
        )
        return ComponentImportResponse(
            message=(
                f"Đã khai báo thành phần cho {len(plan.changes)} nhóm (tạo mới {created} nhóm), bị loại {len(rejected)} "
                f"dòng. Đã tính lại {outcome.yarn_count + len(unmatched_codes)} mã, {priced_failed} mã chưa tính được."
            ),
            committed=True,
            import_id=import_id,
            batch_id=batch.batch_code,
            result_file=ImportResultFileBuilder(import_id, [sheet], result_rows).build(),
            **summary,
        )

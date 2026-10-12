"""UC-34 Kiểm tra và lưu dữ liệu từ file (BR-36, BR-41..BR-45)."""

import time

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.file_builders import ImportResultFileBuilder
from backend.features.yarn_costing.builders.workbook_reader_builder import WorkbookReaderBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.import_business import ImportBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.constants import (
    ALLOWED_EXTENSIONS,
    LEGACY_STAGE_COLUMNS,
    MAX_SHEET_ROWS,
    MAX_UPLOAD_MB,
    SHEET_ORDER,
)
from backend.features.yarn_costing.dto.import_dto import (
    ImportResultResponse,
    ImportWorkbookRequest,
    RejectedRowDTO,
    SheetResultDTO,
)
from backend.features.yarn_costing.exceptions import ImportFileError, YarnValidationError
from backend.features.yarn_costing.models.enums import GroupCode, ImportMode, PriceEvent, RecoveryType
from backend.features.yarn_costing.models.legacy_price import ImportBatch, LegacyPrice, SheetCount
from backend.features.yarn_costing.models.master_checks import FileCheck
from backend.features.yarn_costing.models.rate_version import RateVersion
from backend.features.yarn_costing.models.recovery_rate import RecoveryRate
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.legacy_price_repository import (
    ImportBatchRepository,
    LegacyPriceRepository,
)
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.process_route_repository import ProcessRouteRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.recovery_rate_repository import RecoveryRateRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class ImportWorkbookService(BaseService[ImportWorkbookRequest, ImportResultResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.importer = ImportBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: ImportWorkbookRequest) -> ImportResultResponse:
        started = time.perf_counter()
        a, factory, file = request.actor, request.factory_code, request.file
        group = self.access.authenticate(a.group_code, a.access_code, a.person_name, UserGroupRepository().list_all())
        self.access.ensure_permission(group, "UC-34")
        self.access.ensure_factory_scope(group, factory.value)
        if request.mode == ImportMode.BAN_DAU:
            self.access.ensure_initial_import_allowed(group)
        is_so = group.code == GroupCode.SO
        self.importer.ensure_file_valid(
            FileCheck(extension_ok=file.extension in ALLOWED_EXTENSIONS, size_ok=0 < file.size_mb <= MAX_UPLOAD_MB)
        )
        stages = StageRepository().for_factory(factory.value)
        codes = [s.stage_code for s in stages if not s.is_packaging]
        codes += [c for c in LEGACY_STAGE_COLUMNS.get(factory.value, {}) if c not in codes]  # BR-58 / BR-59
        book = WorkbookReaderBuilder(file, factory, codes).build()
        self.logger.info("Read %s: sheets=%s", file.filename, [(s.sheet, s.read) for s in book.sheets])
        self.importer.ensure_file_valid(
            FileCheck(extension_ok=True, size_ok=True, rows_ok=all(s.read <= MAX_SHEET_ROWS for s in book.sheets))
        )
        if not book.sheets:
            raise ImportFileError("File không có sheet nào đúng tên như file mẫu. Hãy dùng file mẫu.")
        missing_sheets = [s for s in SHEET_ORDER if not book.has_sheet(s)]
        if request.mode == ImportMode.BAN_DAU and missing_sheets:
            raise YarnValidationError(f"File thiếu sheet: {', '.join(missing_sheets)}.")
        problems = [
            f"Sheet '{s.sheet}' thiếu cột bắt buộc: {', '.join(s.missing_columns)}."
            for s in book.sheets
            if s.missing_columns and not self.importer.sheet_skip_message(s.sheet, is_so)
        ]
        if problems:
            raise ImportFileError(" ".join(problems))
        yarns = self.repository.list_all()
        label = self.access.actor_label(group, a.person_name)
        now = utc_now()
        plan = self.importer.plan(
            book,
            factory,
            is_so,
            stages,
            PackagingTypeRepository().list_all(),
            ProcessRouteRepository().list_all(),
            LossGroupRepository().list_all(),
            yarns,
            label,
            now,
        )
        sheets = [SheetResultDTO(**s.model_dump()) for s in plan.sheets]
        rejected = [RejectedRowDTO(**r.model_dump()) for r in plan.rejected_rows]
        created, updated = sum(s.created for s in sheets), sum(s.updated for s in sheets)
        bad = sum(s.rejected for s in sheets)
        self.logger.info("Import plan %s: created=%s updated=%s rejected=%s", file.filename, created, updated, bad)
        if not request.commit:
            return ImportResultResponse(
                message=(
                    f"Kiểm tra file {file.filename}: {plan.valid_count} dòng hợp lệ (tạo {created}, cập nhật {updated}), "
                    f"bị loại {bad} dòng. Bấm 'Lưu {plan.valid_count} dòng hợp lệ' để lưu."
                ),
                sheets=sheets,
                rejected_rows=rejected,
                valid_count=plan.valid_count,
            )
        reason = f"Nhập từ file {file.filename}"
        if plan.rate_lines is not None:
            versions = RateVersionRepository()
            versions.add(
                RateVersion(
                    version_code=self.master.version_code(factory.value, [v.version_code for v in versions.list_all()]),
                    factory_code=factory,
                    effective_date=request.cutoff_date,
                    reason=reason,
                    created_by=label,
                    lines=plan.rate_lines,
                )
            )
        if plan.recovery_rates:
            recovery_repo = RecoveryRateRepository()
            current = {r.recovery_type.value: r for r in recovery_repo.for_factory(factory.value)}
            recovery_repo.save_many(
                [
                    current[k].model_copy(update={"rate": v})
                    if k in current
                    else RecoveryRate(factory_code=factory, recovery_type=RecoveryType(k), rate=v)
                    for k, v in plan.recovery_rates.items()
                ]
            )
        if plan.packaging:
            PackagingTypeRepository().save_many(plan.packaging)
        if plan.routes:
            ProcessRouteRepository().save_many(plan.routes)
        if plan.loss_groups:
            LossGroupRepository().save_many(plan.loss_groups)
        changed = {y.id: y for y in plan.yarns}
        merged = [changed.get(y.id, y) for y in yarns] + [y for y in plan.yarns if y.id not in {x.id for x in yarns}]
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        outcome = self.recalc.recalculate(
            merged,
            load_factory_data(factory),
            PriceEvent.NHAP_TU_FILE,
            now,
            request.cutoff_date,
            changed_by=label,
            batch_id=self.recalc.batch_code(factory.value, codes),
            reason=reason,
        )
        changed.update({y.id: y for y in outcome.yarns})
        self.repository.store(yarns, list(changed.values()))
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.NHAP_TU_FILE, request.cutoff_date, reason, label, outcome, codes
        )
        batch_repo.add(batch)
        import_repo = ImportBatchRepository()
        prefix = f"NF-{factory.value}-"
        numbers = [
            int(b.batch_code[len(prefix) :])
            for b in import_repo.list_all()
            if b.batch_code.startswith(prefix) and b.batch_code[len(prefix) :].isdigit()
        ]
        import_id = f"{prefix}{max(numbers, default=0) + 1:03d}"
        LegacyPriceRepository().save_many(
            [
                LegacyPrice(
                    import_id=import_id,
                    factory_code=factory,
                    yarn_code=code,
                    cost=row.cost,
                    total=row.total if row.total is not None else row.cost.total,
                    priced_date_text=row.priced_date_text,
                )
                for code, row in zip(plan.legacy_codes, plan.legacy_prices, strict=True)
            ]
        )
        import_repo.add(
            ImportBatch(
                batch_code=import_id,
                factory_code=factory,
                mode=request.mode,
                cutoff_date=request.cutoff_date,
                file_name=file.filename,
                imported_by=label,
                sheets=[SheetCount(**s.model_dump()) for s in sheets],
            )
        )
        priced = outcome.yarn_count - outcome.failed_yarn_count
        AuditLogRepository().add(
            self.access.audit_entry(
                group,
                a.person_name,
                "UC-34",
                f"{factory.value} / {import_id}",
                f"{file.filename}: tạo {created}, cập nhật {updated}, bị loại {bad}; lần tính lại {batch.batch_code}",
            )
        )
        self.logger.info(
            "Import %s committed in %.1f s: priced=%s failed=%s",
            import_id,
            time.perf_counter() - started,
            priced,
            outcome.failed_yarn_count,
        )
        return ImportResultResponse(
            message=(
                f"Đã nhập file {file.filename}: tạo {created}, cập nhật {updated}, bị loại {bad} dòng. "
                f"Đã tính giá {priced} mã, {outcome.failed_yarn_count} mã chưa tính được."
            ),
            committed=True,
            sheets=sheets,
            rejected_rows=rejected,
            valid_count=plan.valid_count,
            import_id=import_id,
            result_file=ImportResultFileBuilder(import_id, sheets, rejected).build(),
        )

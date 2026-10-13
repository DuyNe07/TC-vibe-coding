"""UC-05 Khai báo loại đóng gói (BR-62: chỉ tính lại khi Phút/kg của loại đang dùng thay đổi; preview = nội dung hộp xác nhận)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import PACKAGING_NO_RECALC_TEXT, MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse
from backend.features.yarn_costing.dto.master_dto import SavePackagingTypesRequest
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class SavePackagingTypesService(BaseService[SavePackagingTypesRequest, RecalcResultResponse]):
    def __init__(self, repository: PackagingTypeRepository | None = None) -> None:
        self.repository = repository or PackagingTypeRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: SavePackagingTypesRequest) -> RecalcResultResponse:
        factory = request.factory_code
        self.access.ensure_allowed(self.current_user, "UC-05", factory.value)
        old = {p.code: p for p in self.repository.for_factory(factory.value)}
        rows = [r for r in request.rows if r.code and r.code.strip()]
        items = []
        for r in rows:
            code = r.code.strip()
            minutes = r.minutes_per_kg if r.minutes_per_kg is not None else 0
            self.master.require(minutes > 0, "Phút/kg phải lớn hơn 0.")
            item = PackagingType(
                factory_code=factory,
                code=code,
                name=(r.name or code).strip(),
                weight_kg=r.weight_kg,
                man_days=r.man_days,
                minutes_per_kg=minutes,
                active=r.active,
                is_default=r.is_default,
            )
            if code in old:
                item = item.model_copy(update={"id": old[code].id, "created_at": old[code].created_at})
            items.append(item)
        self.master.ensure_valid_packaging(factory.value, items)
        self.master.ensure_single_default(items)
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        in_use = self.master.packaging_in_use(factory.value, yarns)
        new_codes = {i.code for i in items}
        for code in old:
            if code not in new_codes and code in in_use:
                count = sum(1 for y in yarns if y.factory_code == factory and y.packaging_code == code)
                self.master.require(False, f"Không xoá được loại đóng gói {code}: đang được dùng bởi {count} mã sợi.")
        changed_minutes = self.master.packaging_recalc_codes(old, items, in_use)
        if changed_minutes:
            self.master.require_date_and_reason(request.effective_date, request.reason)
        confirm_text = self.master.packaging_confirm_text(factory.value, changed_minutes, request.effective_date)
        if request.preview:
            self.logger.info(
                "Packaging types %s preview: recalculate=%s %s", factory, bool(changed_minutes), changed_minutes
            )
            return RecalcResultResponse(
                message=confirm_text, will_recalculate=bool(changed_minutes), confirm_text=confirm_text
            )
        for code, item in old.items():
            if code not in new_codes:
                self.repository.delete(item.id)
        self.repository.save_many(items)
        version = RateVersionRepository().current(factory.value)
        missing = [i.code for i in items if version is None or version.line_for(i.code) is None]
        label = self.access.user_label(self.current_user)
        batch = None
        outcome_count = failed = 0
        if changed_minutes:
            batch_repo = RecalcBatchRepository()
            codes = [b.batch_code for b in batch_repo.list_all()]
            outcome = self.recalc.recalculate(
                yarns,
                load_factory_data(factory),
                PriceEvent.DOI_DU_LIEU_NEN,
                utc_now(),
                request.effective_date,  # type: ignore[arg-type]
                changed_by=label,
                batch_id=self.recalc.batch_code(factory.value, codes),
                reason=request.reason,
            )
            yarn_repo.store(yarns, outcome.yarns)
            PriceHistoryRepository().add_many(outcome.history)
            batch = self.recalc.make_batch(
                factory, PriceEvent.DOI_DU_LIEU_NEN, request.effective_date, request.reason, label, outcome, codes
            )  # type: ignore[arg-type]
            batch_repo.add(batch)
            outcome_count, failed = outcome.yarn_count, outcome.failed_yarn_count
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                "UC-05",
                factory.value,
                f"Loại đóng gói: {', '.join(sorted(new_codes))}",
                request.reason,
            )
        )
        message = f"Đã lưu loại đóng gói {factory.value}."
        if batch is not None:
            message += f" Đã tính lại {outcome_count} mã, {failed} mã chưa tính được."
        else:
            message += f" {PACKAGING_NO_RECALC_TEXT}"
        for code in missing:
            message += f" Loại đóng gói {code} chưa có định mức chi phí/phút. Vui lòng bổ sung định mức (UC-04) trước khi dùng."
        self.logger.info("Packaging types %s saved: %s (recalculated=%s)", factory, len(items), batch is not None)
        return RecalcResultResponse(
            message=message,
            batch=batch_dto(batch) if batch else None,
            batches=[batch_dto(batch)] if batch else [],
            recalculated_count=outcome_count,
            failed_count=failed,
            will_recalculate=batch is not None,
            confirm_text=confirm_text,
        )

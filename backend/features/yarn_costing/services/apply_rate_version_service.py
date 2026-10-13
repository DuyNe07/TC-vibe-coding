"""UC-04 Áp dụng định mức chi phí/phút mới (+ tính lại toàn bộ xưởng)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.dto_builders import batch_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.recalc_business import RecalcBusiness
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse
from backend.features.yarn_costing.dto.master_dto import ApplyRateVersionRequest
from backend.features.yarn_costing.models.enums import PriceEvent
from backend.features.yarn_costing.models.rate_version import RateLine, RateVersion
from backend.features.yarn_costing.repositories.factory_data_loader import load_factory_data
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository, RecalcBatchRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class ApplyRateVersionService(BaseService[ApplyRateVersionRequest, RecalcResultResponse]):
    def __init__(self, repository: RateVersionRepository | None = None) -> None:
        self.repository = repository or RateVersionRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()
        self.recalc = RecalcBusiness()

    def execute(self, request: ApplyRateVersionRequest) -> RecalcResultResponse:
        factory = request.factory_code
        self.access.ensure_allowed(self.current_user, "UC-04", factory.value)
        rows = [r for r in request.rows if r.rate_code and r.rate_code.strip()]
        values = [(r.labor, r.depreciation, r.electricity, r.materials, r.overhead) for r in rows]
        negative = any(v is None or v < 0 for row in values for v in row)
        lines = (
            []
            if negative
            else [
                RateLine(
                    rate_code=r.rate_code.strip(),
                    labor=r.labor,  # type: ignore[arg-type]
                    depreciation=r.depreciation,  # type: ignore[arg-type]
                    electricity=r.electricity,  # type: ignore[arg-type]
                    materials=r.materials,  # type: ignore[arg-type]
                    overhead=r.overhead,  # type: ignore[arg-type]
                    note=r.note or "",
                )
                for r in rows
            ]
        )
        required = self.master.required_rate_codes(
            StageRepository().for_factory(factory.value), PackagingTypeRepository().for_factory(factory.value)
        )
        self.master.ensure_valid_rate_version(lines, required, negative, request.effective_date, request.reason)
        label = self.access.user_label(self.current_user)
        version = RateVersion(
            version_code=self.master.version_code(factory.value, [v.version_code for v in self.repository.list_all()]),
            factory_code=factory,
            effective_date=request.effective_date,  # type: ignore[arg-type]
            reason=request.reason.strip(),
            created_by=label,
            lines=lines,
        )
        self.repository.add(version)
        now = utc_now()
        yarn_repo = YarnRepository()
        yarns = yarn_repo.list_all()
        batch_repo = RecalcBatchRepository()
        codes = [b.batch_code for b in batch_repo.list_all()]
        code = self.recalc.batch_code(factory.value, codes)
        outcome = self.recalc.recalculate(
            yarns,
            load_factory_data(factory),
            PriceEvent.DOI_DINH_MUC,
            now,
            version.effective_date,
            changed_by=label,
            batch_id=code,
            reason=version.reason,
        )
        yarn_repo.store(yarns, outcome.yarns)
        PriceHistoryRepository().add_many(outcome.history)
        batch = self.recalc.make_batch(
            factory, PriceEvent.DOI_DINH_MUC, version.effective_date, version.reason, label, outcome, codes
        )
        batch_repo.add(batch)
        AuditLogRepository().add(
            self.access.audit_entry(
                self.current_user,
                "UC-04",
                f"{factory.value} / {version.version_code}",
                f"{len(lines)} dòng định mức; lần tính lại {batch.batch_code}",
                version.reason,
            )
        )
        self.logger.info(
            "Rate version %s applied (%s lines); recalculated %s yarns",
            version.version_code,
            len(lines),
            outcome.yarn_count,
        )
        day = version.effective_date.strftime("%d/%m/%Y")
        return RecalcResultResponse(
            message=(
                f"Đã áp dụng định mức mới cho {factory.value} từ ngày {day}. "
                f"Đã tính lại {outcome.yarn_count} mã, {outcome.failed_yarn_count} mã chưa tính được."
            ),
            batch=batch_dto(batch),
            batches=[batch_dto(batch)],
            recalculated_count=outcome.yarn_count,
            failed_count=outcome.failed_yarn_count,
        )

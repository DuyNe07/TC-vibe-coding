"""UC-16 Sửa yêu cầu (chỉ khi 'Chờ xưởng xem')."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import yarn_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, collapse_spaces
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness, upper_name
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.dto.request_dto import UpdateYarnRequestRequest, YarnResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.name_check_repository import (
    NamePartRepository,
    NameWordRepository,
    PendingWordRepository,
)
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class UpdateYarnRequestService(BaseService[UpdateYarnRequestRequest, YarnResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.names = YarnNameBusiness()
        self.requests = RequestBusiness()
        self.master = MasterBusiness()

    def execute(self, request: UpdateYarnRequestRequest) -> YarnResponse:
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy yêu cầu {request.yarn_code}.")
        self.access.ensure_allowed(self.current_user, "UC-16", yarn.factory_code.value)
        self.requests.ensure_pending(yarn)
        name = upper_name(request.yarn_name)  # BR-101 (bổ sung 2026-11-11)
        parsed = self.names.analyze(name)
        self.names.ensure_valid(parsed)
        checks = NameCheckBusiness()
        standard, misspellings = NameWordRepository().lookups(checks.word_uses(yarns))
        name_check = checks.check(name, standard, misspellings)
        word_reason = checks.ensure_request_name(name_check, request.unknown_word_reason)
        version = RateVersionRepository().current(yarn.factory_code.value)
        packaging = {p.code: p for p in PackagingTypeRepository().for_factory(yarn.factory_code.value)}
        chosen = packaging.get(request.packaging_code.strip())
        self.master.require(
            chosen is not None and self.master.is_selectable(chosen, version),
            "Vui lòng chọn loại đóng gói đang dùng của xưởng.",
        )
        updated = yarn.model_copy(
            update={
                "yarn_name": name,
                "yarn_group": parsed.yarn_group,
                "count": parsed.count,
                "loss_group_key": parsed.loss_group_key,
                "technology": self.names.technology(name),
                "is_compact": parsed.is_compact,
                "packaging_code": chosen.code,  # type: ignore[union-attr]
                "customer_name": yarn.customer_name
                if request.customer_name is None
                else collapse_spaces(request.customer_name),
                "unknown_word_reason": word_reason,
                "name_mode": request.name_mode or yarn.name_mode,
            }
        )
        self.master.require(len(updated.customer_name) <= 100, "Khách hàng tối đa 100 ký tự.")
        self.requests.ensure_unique_name(updated, yarns)
        self.repository.store(yarns, [updated])
        label = self.access.user_label(self.current_user)
        if name_check.unknown:  # BR-104
            PendingWordRepository().record([u.word for u in name_check.unknown], yarn.yarn_code, label, word_reason)
        parts = NamePartRepository()
        new_group = checks.new_group(name, parts.list_all()) if parts.list_all() else None
        if new_group is not None:  # BR-102
            parts.add(new_group)
        detail = f"{yarn.yarn_name} / {yarn.packaging_code} → {name} / {updated.packaging_code}"
        if updated.customer_name != yarn.customer_name:
            detail += f" / khách {yarn.customer_name or '-'} → {updated.customer_name or '-'}"
        AuditLogRepository().add(self.access.audit_entry(self.current_user, "UC-16", yarn.yarn_code, detail))
        self.logger.info("Yarn request %s updated", yarn.yarn_code)
        return YarnResponse(
            message=f"Đã cập nhật yêu cầu {yarn.yarn_code}.", yarn=yarn_dto(updated, packaging_name=chosen.name)
        )  # type: ignore[union-attr]

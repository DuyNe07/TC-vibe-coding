"""UC-16 Sửa yêu cầu (chỉ khi 'Chờ xưởng xem')."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import yarn_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, collapse_spaces
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.dto.request_dto import UpdateYarnRequestRequest, YarnResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class UpdateYarnRequestService(BaseService[UpdateYarnRequestRequest, YarnResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.names = YarnNameBusiness()
        self.requests = RequestBusiness()
        self.master = MasterBusiness()

    def execute(self, request: UpdateYarnRequestRequest) -> YarnResponse:
        a = request.actor
        yarns = self.repository.list_all()
        yarn = next((y for y in yarns if y.yarn_code == request.yarn_code), None)
        if yarn is None:
            raise YarnNotFoundError(f"Không tìm thấy yêu cầu {request.yarn_code}.")
        group = self.access.verify(
            a.group_code,
            a.access_code,
            a.person_name,
            UserGroupRepository().list_all(),
            "UC-16",
            yarn.factory_code.value,
        )
        self.requests.ensure_pending(yarn)
        name = collapse_spaces(request.yarn_name)
        parsed = self.names.analyze(name)
        self.names.ensure_valid(parsed)
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
            }
        )
        self.requests.ensure_unique_name(updated, yarns)
        self.repository.store(yarns, [updated])
        detail = f"{yarn.yarn_name} / {yarn.packaging_code} → {name} / {updated.packaging_code}"
        AuditLogRepository().add(self.access.audit_entry(group, a.person_name, "UC-16", yarn.yarn_code, detail))
        self.logger.info("Yarn request %s updated", yarn.yarn_code)
        return YarnResponse(
            message=f"Đã cập nhật yêu cầu {yarn.yarn_code}.", yarn=yarn_dto(updated, packaging_name=chosen.name)
        )  # type: ignore[union-attr]

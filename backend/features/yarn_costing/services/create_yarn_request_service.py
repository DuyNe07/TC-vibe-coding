"""UC-15 Tạo yêu cầu tính giá."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import yarn_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, collapse_spaces
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.constants import FACTORY_NAMES
from backend.features.yarn_costing.dto.request_dto import CreateYarnRequestRequest, YarnResponse
from backend.features.yarn_costing.models.enums import YarnOrigin, YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

PACKAGING_MESSAGE = "Vui lòng chọn loại đóng gói đang dùng của xưởng."


class CreateYarnRequestService(BaseService[CreateYarnRequestRequest, YarnResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.access = AccessBusiness()
        self.names = YarnNameBusiness()
        self.requests = RequestBusiness()
        self.master = MasterBusiness()

    def execute(self, request: CreateYarnRequestRequest) -> YarnResponse:
        factory = request.factory_code
        self.access.ensure_allowed(self.current_user, "UC-15", factory.value)
        name = collapse_spaces(request.yarn_name)
        parsed = self.names.analyze(name)
        self.names.ensure_valid(parsed)
        version = RateVersionRepository().current(factory.value)
        packaging = {p.code: p for p in PackagingTypeRepository().for_factory(factory.value)}
        chosen = packaging.get(request.packaging_code.strip())
        self.master.require(chosen is not None and self.master.is_selectable(chosen, version), PACKAGING_MESSAGE)
        yarns = self.repository.list_all()
        label = self.access.user_label(self.current_user)
        code = self.requests.next_base_code(factory, yarns)
        yarn = Yarn(
            factory_code=factory,
            yarn_code=code,
            base_code=code,
            yarn_name=name,
            yarn_group=parsed.yarn_group,
            count=parsed.count,
            loss_group_key=parsed.loss_group_key,
            technology=self.names.technology(name),
            is_compact=parsed.is_compact,
            packaging_code=chosen.code,  # type: ignore[union-attr]
            status=YarnStatus.CHO_XUONG_XEM,
            origin=YarnOrigin.YEU_CAU_SALES,
            requested_by=label,
        )
        self.requests.ensure_unique_name(yarn, yarns)
        self.repository.store(yarns, [yarn])
        AuditLogRepository().add(
            self.access.audit_entry(self.current_user, "UC-15", code, f"{name} / {yarn.packaging_code}")
        )
        self.logger.info("Yarn request %s created for %s (%s)", code, factory, name)
        return YarnResponse(
            message=f"Đã gửi yêu cầu {code} - {name} cho {FACTORY_NAMES[factory.value]}.",
            yarn=yarn_dto(yarn, packaging_name=chosen.name),  # type: ignore[union-attr]
        )

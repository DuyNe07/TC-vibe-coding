"""UC-42 Kiểm tra điều kiện gửi yêu cầu (BR-63), không lưu gì."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.dto.request_dto import CheckRequestSubmitRequest, RequestSubmitCheckResponse
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository


class CheckRequestSubmitService(BaseService[CheckRequestSubmitRequest, RequestSubmitCheckResponse]):
    def __init__(self, repository: UserGroupRepository | None = None) -> None:
        self.repository = repository or UserGroupRepository()
        self.requests = RequestBusiness()
        self.master = MasterBusiness()

    def execute(self, request: CheckRequestSubmitRequest) -> RequestSubmitCheckResponse:
        groups = {g.code.value: g for g in self.repository.list_all()}
        group = groups.get(request.group_code) if request.group_code else None
        factory = request.factory_code.value if request.factory_code else None
        selectable = False
        if factory:
            version = RateVersionRepository().current(factory)
            selectable = any(
                self.master.is_selectable(p, version) for p in PackagingTypeRepository().for_factory(factory)
            )
        reasons = self.requests.submit_block_reasons(group, groups.get("SALES"), factory, selectable)
        self.logger.info(
            "Submit check: group=%s factory=%s selectable packaging=%s -> %s reason(s)",
            request.group_code,
            factory,
            selectable,
            len(reasons),
        )
        return RequestSubmitCheckResponse(allowed=not reasons, reasons=reasons)

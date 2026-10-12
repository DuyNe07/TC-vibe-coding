"""UC-14 Xoá nhóm tiêu hao (BR-29)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.loss_business import LossBusiness
from backend.features.yarn_costing.dto.common_dto import SaveCountResponse
from backend.features.yarn_costing.dto.loss_dto import DeleteLossGroupRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class DeleteLossGroupService(BaseService[DeleteLossGroupRequest, SaveCountResponse]):
    def __init__(self, repository: LossGroupRepository | None = None) -> None:
        self.repository = repository or LossGroupRepository()
        self.access = AccessBusiness()
        self.business = LossBusiness()

    def execute(self, request: DeleteLossGroupRequest) -> SaveCountResponse:
        a, factory = request.actor, request.factory_code
        group = self.access.verify(
            a.group_code, a.access_code, a.person_name, UserGroupRepository().list_all(), "UC-14", factory.value
        )
        groups = self.repository.for_factory(factory.value)
        target = next((g for g in groups if g.group_key == request.group_key), None)
        if target is None:
            raise YarnNotFoundError(f"Không tìm thấy nhóm tiêu hao '{request.group_key}' ở xưởng {factory.value}.")
        yarn_count = sum(
            1 for y in YarnRepository().list_all() if y.factory_code == factory and y.loss_group_key == target.group_key
        )
        parents = self.business.parents_of(target.group_key, groups)
        self.business.ensure_deletable(yarn_count, len(parents))
        self.repository.delete(target.id)
        AuditLogRepository().add(
            self.access.audit_entry(group, a.person_name, "UC-14", f"{factory.value} / {target.group_key}", "Đã xoá")
        )
        self.logger.info("Loss group %s/%s deleted", factory, target.group_key)
        return SaveCountResponse(message=f"Đã xoá nhóm tiêu hao '{target.group_key}'.", saved_count=1)

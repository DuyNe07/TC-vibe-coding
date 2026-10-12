"""UC-39 Xác thực người thao tác (BR-46)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.dto.user_dto import ActorResponse, VerifyActorRequest
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository


class VerifyActorService(BaseService[VerifyActorRequest, ActorResponse]):
    def __init__(self, repository: UserGroupRepository | None = None) -> None:
        self.repository = repository or UserGroupRepository()
        self.access = AccessBusiness()

    def execute(self, request: VerifyActorRequest) -> ActorResponse:
        a = request.actor
        group = self.access.authenticate(a.group_code, a.access_code, a.person_name, self.repository.list_all())
        self.logger.info("Actor verified: %s - %s", group.code, a.person_name)
        return ActorResponse(
            message=f"Đang thao tác: {group.name} - {a.person_name}.",
            group_code=group.code.value,
            group_name=group.name,
            person_name=a.person_name,
            factory_code=group.factory_code.value if group.factory_code else None,
        )

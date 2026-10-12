"""UC-01 Khai báo nhóm người dùng và thành viên."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import group_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.dto.user_dto import SaveUserGroupRequest, UserGroupResponse
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.user_group import GroupMember
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository


class SaveUserGroupService(BaseService[SaveUserGroupRequest, UserGroupResponse]):
    def __init__(self, repository: UserGroupRepository | None = None) -> None:
        self.repository = repository or UserGroupRepository()
        self.access = AccessBusiness()
        self.master = MasterBusiness()

    def execute(self, request: SaveUserGroupRequest) -> UserGroupResponse:
        a = request.actor
        groups = self.repository.list_all()
        actor_group = self.access.verify(a.group_code, a.access_code, a.person_name, groups, "UC-01")
        group = next((g for g in groups if g.code.value == request.group_code), None)
        if group is None:
            raise YarnNotFoundError(f"Không tìm thấy nhóm '{request.group_code}'.")
        name = " ".join(request.name.split())
        self.master.require(0 < len(name) <= 100, "Tên nhóm bắt buộc và tối đa 100 ký tự.")
        members = [m for m in request.members if m.name and m.name.strip()]
        self.master.ensure_unique_members([m.name for m in members])
        self.master.require(all(len(m.name.strip()) <= 100 for m in members), "Tên thành viên tối đa 100 ký tự.")
        update: dict = {
            "name": name,
            "active": request.active,
            "members": [GroupMember(name=" ".join(m.name.split()), active=m.active) for m in members],
        }
        code_changed = bool(request.new_access_code and request.new_access_code.strip())
        if code_changed:
            self.master.ensure_access_code(request.new_access_code or "")
            update["access_code"] = (request.new_access_code or "").strip()
        saved = self.repository.update(group.model_copy(update=update))
        detail = (
            f"Tên: {group.name} → {saved.name}; Hoạt động: {group.active} → {saved.active}; "
            f"Thành viên: {len(group.members)} → {len(saved.members)}" + ("; Đã đổi mã nội bộ" if code_changed else "")
        )
        AuditLogRepository().add(self.access.audit_entry(actor_group, a.person_name, "UC-01", saved.code.value, detail))
        self.logger.info(
            "Saved user group %s (%s members, access code changed=%s)", saved.code, len(saved.members), code_changed
        )
        return UserGroupResponse(message=f"Đã lưu nhóm {saved.name}.", group=group_dto(saved))

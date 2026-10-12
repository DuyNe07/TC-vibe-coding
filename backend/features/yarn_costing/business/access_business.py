"""BR-46 xác thực thao tác, BR-47 quyền theo nhóm, BR-48 phạm vi xưởng, BR-49 nhật ký."""

from collections.abc import Sequence

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.constants import USE_CASE_ACTIONS, USE_CASE_PERMISSIONS
from backend.features.yarn_costing.models.access import ActorCheck, FactoryScopeCheck, PermissionCheck
from backend.features.yarn_costing.models.audit_log import AuditLog
from backend.features.yarn_costing.models.user_group import UserGroup


class ActorRule(BaseBusinessRule[ActorCheck]):
    code = "BR-46"
    message = "Vui lòng chọn nhóm, nhập đúng mã nội bộ và chọn tên của bạn."

    def is_satisfied_by(self, target: ActorCheck) -> bool:
        return target.is_authenticated


class GroupPermissionRule(BaseBusinessRule[PermissionCheck]):
    code = "BR-47"
    message = "Nhóm không được thực hiện thao tác này."

    def is_satisfied_by(self, target: PermissionCheck) -> bool:
        return target.allowed

    def describe_violation(self, target: PermissionCheck) -> str:
        return f"Nhóm '{target.group_name}' không được thực hiện thao tác này."


class FactoryScopeRule(BaseBusinessRule[FactoryScopeCheck]):
    code = "BR-48"
    message = "Bạn chỉ được thao tác dữ liệu của xưởng mình."

    def is_satisfied_by(self, target: FactoryScopeCheck) -> bool:
        return target.in_scope

    def describe_violation(self, target: FactoryScopeCheck) -> str:
        return f"Bạn chỉ được thao tác dữ liệu của xưởng {target.group_factory}."


class AccessBusiness(BaseBusiness[ActorCheck]):
    def rules(self) -> Sequence[BaseBusinessRule[ActorCheck]]:
        return (ActorRule(),)

    def authenticate(
        self, group_code: str, access_code: str, person_name: str, groups: Sequence[UserGroup]
    ) -> UserGroup:
        """BR-46: nhóm đang hoạt động + đúng mã nội bộ + tên thành viên đang hoạt động."""
        group = next((g for g in groups if g.code == group_code), None)
        check = ActorCheck(
            group_found=group is not None,
            group_active=bool(group and group.active),
            access_code_ok=bool(group and group.access_code == (access_code or "").strip()),
            member_ok=bool(group and person_name in group.active_member_names),
        )
        self.ensure_valid(check)
        assert group is not None
        return group

    def ensure_permission(self, group: UserGroup, use_case: str) -> None:
        """BR-47: Sales → UC-15..17; Xưởng → UC-11..14, 18, 20, 21, 23..26, 28, 34; Kế toán → UC-28; SO → mọi UC."""
        allowed = group.code.value in USE_CASE_PERMISSIONS.get(use_case, ("SO",))
        GroupPermissionRule().check(
            PermissionCheck(group_code=group.code.value, group_name=group.name, use_case=use_case, allowed=allowed)
        )

    def ensure_initial_import_allowed(self, group: UserGroup) -> None:
        """BR-45 / BR-47: 'Chuyển dữ liệu ban đầu' chỉ Phòng SO."""
        allowed = group.code.value == "SO"
        GroupPermissionRule().check(
            PermissionCheck(group_code=group.code.value, group_name=group.name, use_case="UC-34", allowed=allowed)
        )

    def ensure_factory_scope(self, group: UserGroup, factory_code: str | None) -> None:
        """BR-48: nhóm Xưởng S1 / S4 chỉ thao tác dữ liệu của xưởng mình."""
        group_factory = group.factory_code.value if group.factory_code else None
        FactoryScopeRule().check(FactoryScopeCheck(group_factory=group_factory, target_factory=factory_code))

    def verify(
        self,
        group_code: str,
        access_code: str,
        person_name: str,
        groups: Sequence[UserGroup],
        use_case: str,
        factory_code: str | None = None,
    ) -> UserGroup:
        """BR-46 + BR-47 + BR-48 in one call (every mutating use case)."""
        group = self.authenticate(group_code, access_code, person_name, groups)
        self.ensure_permission(group, use_case)
        if factory_code is not None:
            self.ensure_factory_scope(group, factory_code)
        return group

    def audit_entry(
        self, group: UserGroup, person_name: str, use_case: str, object_ref: str, detail: str = "", reason: str = ""
    ) -> AuditLog:
        """BR-49: một dòng nhật ký cho mỗi thao tác thay đổi dữ liệu (lúc, nhóm, tên, thao tác, đối tượng, nội dung, lý do)."""
        return AuditLog(
            group_code=group.code.value,
            person_name=person_name,
            action=USE_CASE_ACTIONS.get(use_case, use_case),
            object_ref=object_ref,
            detail=detail[:4000],
            reason=reason,
        )

    def actor_label(self, group: UserGroup, person_name: str) -> str:
        return f"{group.name} - {person_name}"

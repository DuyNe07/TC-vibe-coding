"""BR-47 vai trò được làm thao tác, BR-48 phạm vi xưởng, BR-49 nhật ký (BR-46: thay bằng đăng nhập của ứng dụng)."""

from collections.abc import Sequence

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.current_user import CurrentUser
from backend.features.yarn_costing.constants import (
    FEATURE_KEY,
    SYSTEM_DISPLAY_NAME,
    SYSTEM_USERNAME,
    USE_CASE_ACTIONS,
)
from backend.features.yarn_costing.models.access import (
    ROLE_FACTORY,
    USE_CASE_PERMISSIONS,
    FactoryScopeCheck,
    PermissionCheck,
)
from backend.features.yarn_costing.models.audit_log import AuditLog

SO_ROLE = "SO"


class RolePermissionRule(BaseBusinessRule[PermissionCheck]):
    code = "BR-47"
    message = "Tài khoản của bạn chưa có vai trò cho thao tác này. Hãy nhờ quản trị viên cấp vai trò ở trang /admin."

    def is_satisfied_by(self, target: PermissionCheck) -> bool:
        return target.allowed

    def describe_violation(self, target: PermissionCheck) -> str:
        return (
            f"Tài khoản của bạn chưa có vai trò cho thao tác '{target.action}'. "
            "Hãy nhờ quản trị viên cấp vai trò ở trang /admin."
        )


class FactoryScopeRule(BaseBusinessRule[FactoryScopeCheck]):
    code = "BR-48"
    message = "Bạn chỉ được thao tác dữ liệu của xưởng mình."

    def is_satisfied_by(self, target: FactoryScopeCheck) -> bool:
        return target.in_scope

    def describe_violation(self, target: FactoryScopeCheck) -> str:
        return f"Bạn chỉ được thao tác dữ liệu của xưởng {target.factories_text}."


class AccessBusiness(BaseBusiness[PermissionCheck]):
    def rules(self) -> Sequence[BaseBusinessRule[PermissionCheck]]:
        return (RolePermissionRule(),)

    def ensure_allowed(self, user: CurrentUser | None, use_case: str, factory_code: str | None = None) -> None:
        """BR-47 + BR-48: có ít nhất một vai trò (của chức năng) cho phép thao tác, và vai trò đó đúng xưởng.

        Không có người dùng (mã hệ thống, test) và quản trị viên (làm như Phòng SO) luôn được phép.
        """
        if user is None or user.is_admin:
            return
        permitted = [
            r for r in user.roles_in(FEATURE_KEY) if r == SO_ROLE or r in USE_CASE_PERMISSIONS.get(use_case, (SO_ROLE,))
        ]
        action = USE_CASE_ACTIONS.get(use_case, use_case)
        RolePermissionRule().check(PermissionCheck(use_case=use_case, action=action, allowed=bool(permitted)))
        FactoryScopeRule().check(
            FactoryScopeCheck(role_factories=tuple(ROLE_FACTORY.get(r) for r in permitted), target_factory=factory_code)
        )

    def is_so(self, user: CurrentUser | None) -> bool:
        """Phòng SO: người dùng có vai trò SO, quản trị viên hoặc mã hệ thống (không có người dùng)."""
        return user is None or user.is_admin or SO_ROLE in user.roles_in(FEATURE_KEY)

    def user_label(self, user: CurrentUser | None) -> str:
        """Tên hiện trong các cột "người làm" (requested_by, created_by, handled_by...)."""
        return user.display_name if user else SYSTEM_DISPLAY_NAME

    def audit_entry(
        self, user: CurrentUser | None, use_case: str, object_ref: str, detail: str = "", reason: str = ""
    ) -> AuditLog:
        """BR-49: một dòng nhật ký cho mỗi thao tác thay đổi dữ liệu (lúc, tài khoản, họ tên, thao tác, đối tượng, nội dung, lý do)."""
        return AuditLog(
            username=user.username if user else SYSTEM_USERNAME,
            display_name=self.user_label(user),
            action=USE_CASE_ACTIONS.get(use_case, use_case),
            object_ref=object_ref,
            detail=detail[:4000],
            reason=reason,
        )

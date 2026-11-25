"""BR-51 roles and team, BR-52 who sees a costsheet, BR-53 who approves, BR-31 the owner (or SO, BR-85) edits."""

from collections.abc import Sequence

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.current_user import CurrentUser
from backend.features.woven_costing.constants import FEATURE_KEY, SYSTEM_NAME, SYSTEM_USERNAME
from backend.features.woven_costing.models.access import (
    CREATORS,
    SO_TEAM,
    TEAM_ROLES,
    USE_CASE_NAMES,
    USE_CASE_ROLES,
)
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.dyeing_job import DyeingJob
from backend.features.woven_costing.models.enums import RoleCode

ALL_ROLES = frozenset(r.value for r in RoleCode)
ADMIN_ROLES = frozenset({RoleCode.SO.value, RoleCode.TRUONG_DON_VI.value})
SYSTEM_TEAM = RoleCode.FS1.value


class RoleRule(BaseBusinessRule[Check]):
    """Target text = use case name; ok = the user has a role allowed for it (BR-51)."""

    code = "BR-51"
    message = "Tài khoản của bạn chưa có vai trò cho thao tác này. Liên hệ quản trị viên."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f'Tài khoản của bạn chưa có vai trò cho thao tác "{target.text}". Liên hệ quản trị viên.'


class TeamRule(BaseBusinessRule[Check]):
    """BR-51: a user with SALES or TRUONG_TEAM needs exactly one team to create a costsheet."""

    code = "BR-51"
    message = "Tài khoản của bạn chưa được gán team FS1 / FS2. Liên hệ quản trị viên."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class ViewRule(BaseBusinessRule[Check]):
    code = "BR-52"
    message = "Bạn không có quyền xem costsheet này."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class ApproveRule(BaseBusinessRule[Check]):
    code = "BR-53"
    message = "Bạn không có quyền duyệt costsheet này."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class OwnerRule(BaseBusinessRule[Check]):
    """BR-31: only the owner, or a user with the SO role (BR-85), edits (and only Nháp / Trả lại, see
    WorkflowBusiness)."""

    code = "BR-31"
    message = "Chỉ người lập costsheet được thao tác này."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class AccessBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (RoleRule(),)

    def roles(self, user: CurrentUser | None) -> frozenset[str]:
        """BR-51: roles granted on /admin. System code / tests: every role; administrators: SO + Trưởng đơn vị."""
        if user is None:
            return ALL_ROLES
        own = frozenset(user.roles_in(FEATURE_KEY))
        return own | ADMIN_ROLES if user.all_apps else own

    def username(self, user: CurrentUser | None) -> str:
        return user.username if user else SYSTEM_USERNAME

    def display_name(self, user: CurrentUser | None) -> str:
        return user.display_name if user else SYSTEM_NAME

    def team(self, user: CurrentUser | None) -> str | None:
        """BR-51: the single team (FS1 / FS2) of the user; a user with the SO role and no single team -> "SO";
        None when none (or both) and no SO role."""
        if user is None:
            return SYSTEM_TEAM
        roles = self.roles(user)
        teams = [t for t in TEAM_ROLES if t in roles]
        if len(teams) == 1:
            return teams[0]
        return SO_TEAM if self.is_so(user) else None

    def is_so(self, user: CurrentUser | None) -> bool:
        """BR-85: the user has the SO role (system code counts as SO)."""
        return RoleCode.SO.value in self.roles(user)

    def has_any(self, user: CurrentUser | None, roles: Sequence[str]) -> bool:
        return bool(self.roles(user) & set(roles))

    def ensure_use_case(self, user: CurrentUser | None, use_case: str) -> None:
        """BR-51: the user has one of the roles of the use case actors (section 6)."""
        allowed = USE_CASE_ROLES.get(use_case, ())
        RoleRule().check(Check(ok=self.has_any(user, allowed), text=USE_CASE_NAMES.get(use_case, use_case)))

    def ensure_team(self, user: CurrentUser | None) -> str:
        team = self.team(user)
        TeamRule().check(Check(ok=team is not None))
        return team or ""

    def can_view(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> bool:
        """BR-52: SALES / TRUONG_TEAM see their team (never team "SO"); TRUONG_DON_VI and SO see everything (team
        "SO" included); PD alone sees nothing."""
        roles = self.roles(user)
        if roles & ADMIN_ROLES:
            return True
        if roles & set(CREATORS):
            own_team = sheet.team in TEAM_ROLES and sheet.team in roles
            return own_team or sheet.sales_username == self.username(user)
        return False

    def ensure_view(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> None:
        ViewRule().check(Check(ok=self.can_view(user, sheet)))

    def is_owner(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> bool:
        """BR-31 / BR-52: the creator of the costsheet (system code counts as the owner)."""
        return user is None or sheet.sales_username == user.username

    def can_edit(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> bool:
        """BR-31 / BR-85: the owner (with a creator role) or any user with the SO role works on the costsheet."""
        return (self.is_owner(user, sheet) and self.has_any(user, CREATORS)) or self.is_so(user)

    def ensure_owner(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> None:
        OwnerRule().check(Check(ok=self.can_edit(user, sheet)))

    def can_approve(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> bool:
        """BR-53: TRUONG_TEAM of the costsheet team, TRUONG_DON_VI or SO (own costsheets included; team "SO" only by
        SO or TRUONG_DON_VI). Sales do not approve."""
        roles = self.roles(user)
        if RoleCode.TRUONG_DON_VI.value in roles or RoleCode.SO.value in roles:
            return True
        return RoleCode.TRUONG_TEAM.value in roles and sheet.team in roles

    def ensure_approve(self, user: CurrentUser | None, sheet: Costsheet | DyeingJob) -> None:
        ApproveRule().check(Check(ok=self.can_approve(user, sheet)))

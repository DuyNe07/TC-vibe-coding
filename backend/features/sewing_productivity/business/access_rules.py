"""BR-09: who may change data in this app."""

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.current_user import CurrentUser
from backend.features.sewing_productivity.constants import FEATURE_KEY, MESSAGE_BR09, SYSTEM_USER, UPDATER_ROLE


class UpdaterRoleRule(BaseBusinessRule[CurrentUser | None]):
    code = "BR-09"
    message = MESSAGE_BR09

    def is_satisfied_by(self, target: CurrentUser | None) -> bool:
        if target is None or target.is_admin or target.is_master:  # None = system code and tests
            return True
        return UPDATER_ROLE in target.roles_in(FEATURE_KEY)


class AccessBusiness(BaseBusiness[CurrentUser | None]):
    def rules(self) -> tuple[UpdaterRoleRule, ...]:
        return (UpdaterRoleRule(),)

    def saved_by(self, user: CurrentUser | None) -> str:
        """The name recorded on what a person saves."""
        return user.display_name if user else SYSTEM_USER

    def deleted_by(self, user: CurrentUser | None) -> str | None:
        """The username recorded on what a person flags as deleted (None for system code and tests)."""
        return user.username if user else None

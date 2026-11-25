"""Roles of the logged-in user in this app - only to hide / disable buttons; the backend decides (BR-51)."""

from backend.core.current_user import get_current_user
from backend.features.woven_costing.dto.common_dto import RoleCode

FEATURE_KEY = "woven_costing"
ADMIN_ROLES = frozenset({RoleCode.SO.value, RoleCode.TRUONG_DON_VI.value})


def my_roles() -> frozenset[str] | None:
    """None = no logged-in user (headless test / system): treated as every role, like the backend."""
    user = get_current_user()
    if user is None:
        return None
    roles = frozenset(user.roles_in(FEATURE_KEY))
    return roles | ADMIN_ROLES if user.all_apps else roles


def has_any(*codes: str) -> bool:
    roles = my_roles()
    return roles is None or any(code in roles for code in codes)

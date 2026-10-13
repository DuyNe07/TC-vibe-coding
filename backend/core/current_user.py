"""Who is using the app right now, and what they may open. Set by the UI on every run (``frontend/core/auth.py``).

Permission keys (stored on users and groups):
    "<feature_key>"              the whole feature (every page; NOT its roles)
    "<feature_key>/<page_slug>"  one page of a feature (landing page without slug: "<feature_key>/main")
    "<feature_key>/@<ROLE>"      a role the feature declares in its manifest (e.g. "yarn_costing/@SO"); the feature's
                                 own business rules decide what a role may do (``CurrentUser.roles_in``)

``None`` (no user set) means system code: tests, scripts. The UI never runs a page without a logged-in user.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field

LANDING_PAGE_SLUG = "main"


def page_permission(feature_key: str, page_slug: str) -> str:
    return f"{feature_key}/{page_slug or LANDING_PAGE_SLUG}"


def role_permission(feature_key: str, role: str) -> str:
    return f"{feature_key}/@{role}"


def in_app(permission: str, feature_key: str) -> bool:
    """True when the key is about this app (the whole app, one of its pages or one of its roles)."""
    return permission == feature_key or permission.startswith(f"{feature_key}/")


@dataclass(frozen=True)
class CurrentUser:
    username: str
    full_name: str = ""
    is_admin: bool = False
    permissions: frozenset[str] = field(default_factory=frozenset)  # personal + every group (union)

    @property
    def display_name(self) -> str:
        return self.full_name or self.username

    def can_open_feature(self, feature_key: str) -> bool:
        """True when the user may open at least one page of the feature (gateway check)."""
        return self.is_admin or any(in_app(p, feature_key) for p in self.permissions)

    def roles_in(self, feature_key: str) -> frozenset[str]:
        """Role codes granted in one app (personal + groups). Administrators get none automatically: the app decides."""
        prefix = role_permission(feature_key, "")
        return frozenset(p.removeprefix(prefix) for p in self.permissions if p.startswith(prefix))

    def can_open_page(self, feature_key: str, page_slug: str) -> bool:
        return (
            self.is_admin
            or feature_key in self.permissions
            or page_permission(feature_key, page_slug) in self.permissions
        )


_current: ContextVar[CurrentUser | None] = ContextVar("tc_current_user", default=None)


def get_current_user() -> CurrentUser | None:
    return _current.get()


def set_current_user(user: CurrentUser | None) -> None:
    _current.set(user)

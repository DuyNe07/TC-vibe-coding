"""Who is using the app right now, and what they may open. Set by the UI on every run (``frontend/core/auth.py``).

Permission keys (stored on users and groups):
    "<feature_key>"              the whole feature (every page)
    "<feature_key>/<page_slug>"  one page of a feature (landing page without slug: "<feature_key>/main")

``None`` (no user set) means system code: tests, scripts. The UI never runs a page without a logged-in user.
"""

from contextvars import ContextVar
from dataclasses import dataclass, field

LANDING_PAGE_SLUG = "main"


def page_permission(feature_key: str, page_slug: str) -> str:
    return f"{feature_key}/{page_slug or LANDING_PAGE_SLUG}"


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
        return (
            self.is_admin
            or feature_key in self.permissions
            or any(p.startswith(f"{feature_key}/") for p in self.permissions)
        )

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

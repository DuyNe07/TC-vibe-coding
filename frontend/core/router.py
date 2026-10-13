"""Router: turns the registry into Streamlit pages and URLs.

URLs:  /            -> redirects to /home
       /home        -> Home page (feature cards)
       /<feature>   -> first page of a feature   (feature key with '-' instead of '_')
       /<feature>-<page-slug> -> other pages of the feature
       /admin       -> user & permission administration (admins only, typed by hand: not in the menu)

Only the pages the logged-in user may open are registered: the others have no URL and no menu entry.
"""

from dataclasses import dataclass

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from backend.core.current_user import CurrentUser
from backend.core.exceptions import PermissionDeniedError
from backend.core.naming import feature_url_slug
from frontend.core.base_page import BasePage
from frontend.core.feature_manifest import FeatureManifest
from frontend.core.registry import FeatureRegistry

HOME_URL_PATH = "home"
ADMIN_URL_PATH = "admin"
_ROUTER_KEY = "_tc_router"


@dataclass(frozen=True)
class PageEntry:
    manifest: FeatureManifest
    page_cls: type[BasePage]
    page: StreamlitPage


class Router:
    def __init__(
        self,
        registry: FeatureRegistry,
        home_page: BasePage,
        user: CurrentUser | None = None,
        admin_page: BasePage | None = None,
    ) -> None:
        """``user=None`` (tests) registers every page; otherwise only the pages the user may open."""
        self.registry = registry
        self.user = user
        self.home = st.Page(home_page.run, title=home_page.title, icon=home_page.icon, url_path=HOME_URL_PATH)
        self._root = st.Page(self._redirect_home, title=home_page.title, icon=home_page.icon, default=True)
        self.admin: StreamlitPage | None = None
        if admin_page is not None and user is not None and user.is_admin:
            self.admin = st.Page(admin_page.run, title=admin_page.title, icon=admin_page.icon, url_path=ADMIN_URL_PATH)
        self._entries: list[PageEntry] = []
        for manifest in registry.features:
            base_slug = feature_url_slug(manifest.key)
            for index, page_cls in enumerate(manifest.pages):
                if user is not None and not user.can_open_page(manifest.key, page_cls.slug):
                    continue
                url_path = base_slug if index == 0 else f"{base_slug}-{page_cls.slug}"
                page = st.Page(page_cls(manifest.key).run, title=page_cls.title, icon=page_cls.icon, url_path=url_path)
                self._entries.append(PageEntry(manifest, page_cls, page))
        self.features = [m for m in registry.features if self.entries_of(m.key)]  # features the user can open

    def navigation(self) -> StreamlitPage:
        """Register the allowed pages (menu is drawn by sidebar_nav) and return the current page."""
        extra = [self.admin] if self.admin else []
        return st.navigation([self._root, self.home, *extra, *(e.page for e in self._entries)], position="hidden")

    def groups(self) -> dict[str, list[FeatureManifest]]:
        """Home / sidebar sections with the features the user can open."""
        grouped: dict[str, list[FeatureManifest]] = {}
        for manifest in self.features:
            grouped.setdefault(manifest.group, []).append(manifest)
        return grouped

    def can_open(self, page_cls: type[BasePage]) -> bool:
        return any(entry.page_cls is page_cls for entry in self._entries)

    def entries_of(self, feature_key: str) -> list[PageEntry]:
        return [e for e in self._entries if e.manifest.key == feature_key]

    def landing_page(self, feature_key: str) -> StreamlitPage:
        return self.entries_of(feature_key)[0].page

    def page_for(self, page_cls: type[BasePage]) -> StreamlitPage:
        for entry in self._entries:
            if entry.page_cls is page_cls:
                return entry.page
        if any(page_cls in manifest.pages for manifest in self.registry.features):
            raise PermissionDeniedError(f"No permission to open page '{page_cls.title}'.")
        raise LookupError(f"{page_cls.__name__} is not listed in any FeatureManifest.pages")

    def switch_to(self, page_cls: type[BasePage]) -> None:
        st.switch_page(self.page_for(page_cls))

    def link(self, page_cls: type[BasePage], label: str | None = None, icon: str | None = None) -> None:
        """Link to a page; nothing is shown when the user may not open it."""
        if not self.can_open(page_cls):
            return
        st.page_link(self.page_for(page_cls), label=label or page_cls.title, icon=icon or page_cls.icon)

    def _redirect_home(self) -> None:
        st.switch_page(self.home)


def set_current_router(router: Router) -> None:
    st.session_state[_ROUTER_KEY] = router


def get_router() -> Router:
    return st.session_state[_ROUTER_KEY]

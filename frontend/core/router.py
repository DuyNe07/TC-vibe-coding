"""Router: turns the registry into Streamlit pages and URLs.

URLs:  /            -> redirects to /home
       /home        -> Home page (feature cards)
       /<feature>   -> first page of a feature   (feature key with '-' instead of '_')
       /<feature>-<page-slug> -> other pages of the feature
"""

from dataclasses import dataclass

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from backend.core.naming import feature_url_slug
from frontend.core.base_page import BasePage
from frontend.core.feature_manifest import FeatureManifest
from frontend.core.registry import FeatureRegistry

HOME_URL_PATH = "home"
_ROUTER_KEY = "_tc_router"


@dataclass(frozen=True)
class PageEntry:
    manifest: FeatureManifest
    page_cls: type[BasePage]
    page: StreamlitPage


class Router:
    def __init__(self, registry: FeatureRegistry, home_page: BasePage) -> None:
        self.registry = registry
        self.home = st.Page(home_page.run, title=home_page.title, icon=home_page.icon, url_path=HOME_URL_PATH)
        self._root = st.Page(self._redirect_home, title=home_page.title, icon=home_page.icon, default=True)
        self._entries: list[PageEntry] = []
        for manifest in registry.features:
            base_slug = feature_url_slug(manifest.key)
            for index, page_cls in enumerate(manifest.pages):
                url_path = base_slug if index == 0 else f"{base_slug}-{page_cls.slug}"
                page = st.Page(page_cls(manifest.key).run, title=page_cls.title, icon=page_cls.icon, url_path=url_path)
                self._entries.append(PageEntry(manifest, page_cls, page))

    def navigation(self) -> StreamlitPage:
        """Register all pages (menu is drawn by sidebar_nav) and return the current page."""
        return st.navigation([self._root, self.home, *(e.page for e in self._entries)], position="hidden")

    def entries_of(self, feature_key: str) -> list[PageEntry]:
        return [e for e in self._entries if e.manifest.key == feature_key]

    def landing_page(self, feature_key: str) -> StreamlitPage:
        return self.entries_of(feature_key)[0].page

    def page_for(self, page_cls: type[BasePage]) -> StreamlitPage:
        for entry in self._entries:
            if entry.page_cls is page_cls:
                return entry.page
        raise LookupError(f"{page_cls.__name__} is not listed in any FeatureManifest.pages")

    def switch_to(self, page_cls: type[BasePage]) -> None:
        st.switch_page(self.page_for(page_cls))

    def link(self, page_cls: type[BasePage], label: str | None = None, icon: str | None = None) -> None:
        st.page_link(self.page_for(page_cls), label=label or page_cls.title, icon=icon or page_cls.icon)

    def _redirect_home(self) -> None:
        st.switch_page(self.home)


def set_current_router(router: Router) -> None:
    st.session_state[_ROUTER_KEY] = router


def get_router() -> Router:
    return st.session_state[_ROUTER_KEY]

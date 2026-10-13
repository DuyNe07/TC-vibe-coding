"""Sidebar menu, generated from the feature registry (never edit it to add a feature).

Section (manifest.group) -> one collapsible block per feature (click the arrow to show its pages) -> pages,
optionally under sub-group labels (``BasePage.menu_group``). Only the pages the user may open are listed.
The admin page is never in the menu: administrators open it by URL (/admin), where the sidebar shows only a way back.
"""

from typing import TYPE_CHECKING

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from backend.core.config import get_settings

if TYPE_CHECKING:
    from frontend.core.router import PageEntry, Router


def render_sidebar_nav(router: "Router", current: StreamlitPage | None = None) -> None:
    current_path = current.url_path if current is not None else None
    with st.sidebar:
        st.markdown(f"**{get_settings().name}**")
        on_admin = router.admin is not None and current_path == router.admin.url_path
        if on_admin:
            st.page_link(router.home, label="Về ứng dụng", icon="⬅️")
        else:
            _feature_menu(router, current_path)
        _user_box(router)


def _feature_menu(router: "Router", current_path: str | None) -> None:
    st.page_link(router.home, label="Trang chủ", icon="🏠")
    for group, manifests in router.groups().items():
        st.caption(f"**{group}**")
        for manifest in manifests:
            entries = router.entries_of(manifest.key)
            if len(entries) == 1:
                st.page_link(entries[0].page, label=manifest.title, icon=manifest.icon)
                continue
            is_open = any(e.page.url_path == current_path for e in entries)
            with st.expander(f"{manifest.icon} {manifest.title}", expanded=is_open):
                _page_links(entries)
    if router.registry.errors:
        st.warning(f"{len(router.registry.errors)} chức năng đang lỗi - xem chi tiết ở Trang chủ.", icon="⚠️")


def _user_box(router: "Router") -> None:
    if router.user is None:
        return
    st.divider()
    left, right = st.columns([3, 2], vertical_alignment="center")
    left.caption(f"👤 {router.user.display_name}")
    if right.button("Đăng xuất", key="tc-logout", width="stretch"):
        from frontend.core.auth import logout

        logout()


def _page_links(entries: "list[PageEntry]") -> None:
    """Pages in manifest order; a sub-group label is shown each time ``menu_group`` changes."""
    last_group = ""
    for entry in entries:
        group = entry.page_cls.menu_group
        if group and group != last_group:
            st.caption(group)
        last_group = group
        st.page_link(entry.page, label=entry.page_cls.title, icon=entry.page_cls.icon)

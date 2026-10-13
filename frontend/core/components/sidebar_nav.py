"""Sidebar menu, generated from the feature registry (never edit it to add a feature).

Section (manifest.group) -> one collapsible block per feature (click the arrow to show its pages) -> pages,
optionally under sub-group labels (``BasePage.menu_group``). Only the pages the user may open are listed.
"""

from html import escape
from typing import TYPE_CHECKING

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from backend.core.config import get_settings
from frontend.core.branding import logo_data_uri

if TYPE_CHECKING:
    from frontend.core.router import PageEntry, Router


def render_sidebar_nav(router: "Router", current: StreamlitPage | None = None) -> None:
    settings = get_settings()
    logo_uri = logo_data_uri()
    if logo_uri:
        logo = f'<img class="tc-brand-img" src="{logo_uri}" alt="logo">'
    else:
        initials = "".join(word[0] for word in settings.name.split()[:2]).upper() or "TC"
        logo = f'<div class="tc-brand-logo">{escape(initials)}</div>'
    current_path = current.url_path if current is not None else None
    with st.sidebar:
        st.markdown(
            f"""<div class="tc-brand">{logo}
                  <div><div class="tc-brand-name">{escape(settings.name)}</div>
                  <div class="tc-brand-sub">Cổng công cụ nội bộ</div></div></div>""",
            unsafe_allow_html=True,
        )
        st.page_link(router.home, label="Trang chủ", icon="🏠")
        for group, manifests in router.groups().items():
            st.markdown(f'<div class="tc-nav-group">{escape(group)}</div>', unsafe_allow_html=True)
            for manifest in manifests:
                entries = router.entries_of(manifest.key)
                if len(entries) == 1:
                    st.page_link(entries[0].page, label=manifest.title, icon=manifest.icon)
                    continue
                is_open = any(e.page.url_path == current_path for e in entries)
                with st.expander(f"{manifest.icon} {manifest.title}", expanded=is_open):
                    _page_links(entries)
        if router.admin is not None:
            st.markdown('<div class="tc-nav-group">Quản trị</div>', unsafe_allow_html=True)
            st.page_link(router.admin, label="Người dùng & phân quyền", icon="🛡️")
        if router.registry.errors:
            st.warning(f"{len(router.registry.errors)} chức năng đang lỗi - xem chi tiết ở Trang chủ.", icon="⚠️")
        if router.user is not None:
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
            st.markdown(f'<div class="tc-nav-sub">{escape(group)}</div>', unsafe_allow_html=True)
        last_group = group
        st.page_link(entry.page, label=entry.page_cls.title, icon=entry.page_cls.icon)

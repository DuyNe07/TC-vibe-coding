"""Sidebar menu, generated from the feature registry (never edit it to add a feature)."""

from html import escape
from typing import TYPE_CHECKING

import streamlit as st

from backend.core.config import get_settings
from frontend.core.branding import logo_data_uri

if TYPE_CHECKING:
    from frontend.core.router import Router


def render_sidebar_nav(router: "Router") -> None:
    settings = get_settings()
    logo_uri = logo_data_uri()
    if logo_uri:
        logo = f'<img class="tc-brand-img" src="{logo_uri}" alt="logo">'
    else:
        initials = "".join(word[0] for word in settings.name.split()[:2]).upper() or "TC"
        logo = f'<div class="tc-brand-logo">{escape(initials)}</div>'
    with st.sidebar:
        st.markdown(
            f"""<div class="tc-brand">{logo}
                  <div><div class="tc-brand-name">{escape(settings.name)}</div>
                  <div class="tc-brand-sub">Cổng công cụ nội bộ</div></div></div>""",
            unsafe_allow_html=True,
        )
        st.page_link(router.home, label="Trang chủ", icon="🏠")
        for group, manifests in router.registry.groups().items():
            st.markdown(f'<div class="tc-nav-group">{escape(group)}</div>', unsafe_allow_html=True)
            for manifest in manifests:
                entries = router.entries_of(manifest.key)
                st.page_link(entries[0].page, label=manifest.title, icon=manifest.icon)
                for entry in entries[1:]:
                    st.page_link(entry.page, label=f"↳ {entry.page_cls.title}")
        if router.registry.errors:
            st.warning(f"{len(router.registry.errors)} chức năng đang lỗi - xem chi tiết ở Trang chủ.", icon="⚠️")

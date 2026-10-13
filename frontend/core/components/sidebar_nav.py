"""Sidebar, generated from the feature registry (never edit it to add an app).

Home (/home): only who is logged in - the apps are the cards on the page.
Inside an app (/<app>...): a way back to all apps, the app's name, then its pages under their ``menu_group`` labels.
The admin page (/admin, typed by hand, never in a menu) shows only the way back.
Only the pages the user may open are listed.
"""

from typing import TYPE_CHECKING

import streamlit as st
from streamlit.navigation.page import StreamlitPage

if TYPE_CHECKING:
    from frontend.core.router import PageEntry, Router


def render_sidebar_nav(router: "Router", current: StreamlitPage | None = None) -> None:
    manifest = router.feature_of(current)
    with st.sidebar:
        if current is not None and current.url_path != router.home.url_path:
            st.page_link(router.home, label="Tất cả ứng dụng", icon=":material/apps:")
        if manifest is not None:
            st.subheader(f"{manifest.icon} {manifest.title}", anchor=False)
            _page_links(router.entries_of(manifest.key))
        _user_box(router)


def _page_links(entries: "list[PageEntry]") -> None:
    """Pages in manifest order; a group label is shown each time ``menu_group`` changes."""
    last_group = ""
    for entry in entries:
        group = entry.page_cls.menu_group
        if group and group != last_group:
            st.caption(f"**{group}**")
        last_group = group
        st.page_link(entry.page, label=entry.page_cls.title, icon=entry.page_cls.icon)


def _user_box(router: "Router") -> None:
    if router.user is None:
        return
    st.divider()
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(f":material/account_circle: **{router.user.display_name}**  \n:gray[{router.user.username}]")
        if st.button("Đăng xuất", key="tc-logout", icon=":material/logout:", type="tertiary"):
            from frontend.core.auth import logout

            logout()

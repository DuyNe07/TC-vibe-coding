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
        if st.button("Đổi mật khẩu", key="tc-change-password", icon=":material/key:", type="tertiary"):
            _change_password_dialog(router.user.username)
        if st.button("Đăng xuất", key="tc-logout", icon=":material/logout:", type="tertiary"):
            from frontend.core.auth import logout

            logout()


@st.dialog("Đổi mật khẩu")
def _change_password_dialog(username: str) -> None:
    from backend.core.access import AccessManager
    from backend.core.exceptions import InvalidInputError

    with st.form("tc-change-password-form"):
        old = st.text_input("Mật khẩu hiện tại", type="password")
        new = st.text_input("Mật khẩu mới", type="password")
        again = st.text_input("Nhập lại mật khẩu mới", type="password")
        if not st.form_submit_button("Lưu mật khẩu mới", type="primary", width="stretch"):
            return
    if not new:
        st.error("Mật khẩu mới không được để trống.")
    elif new != again:
        st.error("Hai lần nhập mật khẩu mới không giống nhau.")
    else:
        try:
            AccessManager().change_own_password(username, old, new)
        except InvalidInputError:
            st.error("Mật khẩu hiện tại không đúng.")
        else:
            st.success("Đã đổi mật khẩu. Lần đăng nhập sau dùng mật khẩu mới.")

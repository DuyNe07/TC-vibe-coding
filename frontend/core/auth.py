"""Login screen + the logged-in user of this browser session (applied to every run by AppShell)."""

import streamlit as st

from backend.core.access import AccessManager
from backend.core.config import get_settings
from backend.core.current_user import CurrentUser, set_current_user

_USER_KEY = "_tc_username"


def require_login() -> CurrentUser:
    """Return the logged-in user (rights refreshed on every run); otherwise draw the login form and stop."""
    username = st.session_state.get(_USER_KEY)
    user = AccessManager().refresh(username) if username else None
    if user is None:
        st.session_state.pop(_USER_KEY, None)
        set_current_user(None)
        AccessManager().ensure_admin()  # first start: create u-admin
        _login_form()
        st.stop()
    set_current_user(user)
    return user


def logout() -> None:
    st.session_state.clear()
    set_current_user(None)
    st.rerun()


def _login_form() -> None:
    _, center, _ = st.columns([1, 1.2, 1])
    with center, st.form("tc-login"):
        st.markdown(f"### 🔐 {get_settings().name}")
        st.caption("Đăng nhập để sử dụng các chức năng được cấp quyền.")
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.form_submit_button("Đăng nhập", type="primary", width="stretch"):
            user = AccessManager().authenticate(username, password)
            if user is None:
                st.error("Sai tên đăng nhập hoặc mật khẩu, hoặc tài khoản đã bị khoá.")
            else:
                st.session_state[_USER_KEY] = user.username
                st.rerun()

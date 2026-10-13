"""Login screen + the logged-in user of this browser session (applied to every run by AppShell).

A page reload (F5) opens a new Streamlit session: the user is then restored from the ``tc_session`` cookie, whose
token points to a ``LoginSession`` in the database (expires after ``APP_SESSION_HOURS``; logout deletes it).
"""

import streamlit as st

from backend.core.access import AccessManager
from backend.core.config import get_settings
from backend.core.current_user import CurrentUser, set_current_user
from frontend.core.warm_up import start_warm_up

COOKIE_NAME = "tc_session"
_USER_KEY = "_tc_username"
_TOKEN_KEY = "_tc_session_token"
_COOKIE_JS_KEY = "_tc_cookie_js"  # cookie change to send to the browser on the next run


def require_login() -> CurrentUser:
    """Return the logged-in user (rights refreshed on every run); otherwise draw the login form and stop."""
    start_warm_up()  # fresh server: load the apps and their tables in the background (while the user types)
    access = AccessManager()
    username = st.session_state.get(_USER_KEY)
    user = access.refresh(username) if username else None
    token = st.context.cookies.get(COOKIE_NAME)
    if user is None and not username and isinstance(token, str) and token:
        user = access.resume(token)  # page reloaded: same login while the session is valid
        if user is not None:
            st.session_state[_USER_KEY], st.session_state[_TOKEN_KEY] = user.username, token
    if user is None:
        st.session_state.pop(_USER_KEY, None)
        set_current_user(None)
        _send_cookie_change()
        access.ensure_admin()  # first start: create u-admin
        _login_form(access)
        st.stop()
    _send_cookie_change()
    set_current_user(user)
    return user


def logout() -> None:
    token = st.session_state.get(_TOKEN_KEY)
    if token:
        AccessManager().end_session(token)
    st.session_state.clear()
    st.session_state[_COOKIE_JS_KEY] = f"document.cookie = '{COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Strict';"
    set_current_user(None)
    st.rerun()


def _login_form(access: AccessManager) -> None:
    _, center, _ = st.columns([1, 1.2, 1])
    with center, st.form("tc-login"):
        st.markdown(f"### 🔐 {get_settings().name}")
        st.caption("Đăng nhập để sử dụng các chức năng được cấp quyền.")
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.form_submit_button("Đăng nhập", type="primary", width="stretch"):
            user = access.authenticate(username, password)
            if user is None:
                st.error("Sai tên đăng nhập hoặc mật khẩu, hoặc tài khoản đã bị khoá.")
            else:
                token = access.start_session(user.username)
                max_age = get_settings().session_hours * 3600
                st.session_state[_USER_KEY], st.session_state[_TOKEN_KEY] = user.username, token
                st.session_state[_COOKIE_JS_KEY] = (
                    f"document.cookie = '{COOKIE_NAME}={token}; Path=/; Max-Age={max_age}; SameSite=Strict';"
                )
                st.rerun()


def _send_cookie_change() -> None:
    """Write / delete the cookie in the browser (a rerun would drop a script sent in the same run as st.rerun)."""
    script = st.session_state.pop(_COOKIE_JS_KEY, None)
    if script:
        st.html(f"<script>{script}</script>", unsafe_allow_javascript=True)

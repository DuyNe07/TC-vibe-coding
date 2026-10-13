"""Login screen, permission-filtered menu and the admin page, rendered with Streamlit's headless AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from backend.core.access import AccessManager, User

APP = str(Path(__file__).resolve().parents[2] / "frontend" / "app.py")


def _login(username: str, password: str) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    assert [t.label for t in app.text_input] == ["Tên đăng nhập", "Mật khẩu"], "login form expected first"
    app.text_input[0].input(username)
    app.text_input[1].input(password)
    app.button[0].click().run()
    assert not app.exception, [e.value for e in app.exception]
    return app


def _menu_texts(app: AppTest) -> str:
    return " ".join(str(m.value) for m in app.markdown)


def _page_links(app: AppTest) -> list[str]:
    return [link.proto.label for link in app.get("page_link")]


def test_wrong_password_stays_on_login() -> None:
    app = _login("u-admin", "wrong")
    assert any("Sai tên đăng nhập" in e.value for e in app.error)


def test_admin_page_is_reachable_by_url_only_and_renders() -> None:
    app = _login("u-admin", "u-admin")
    links = set(_page_links(app))
    assert {"Nhập sản phẩm từ Excel", "Danh sách sản phẩm"} <= links
    assert "Người dùng & phân quyền" not in links, "the admin page must not be in the menu (open it by URL /admin)"

    def admin_page() -> None:
        from backend.core.current_user import CurrentUser, set_current_user
        from frontend.core.admin_page import AdminPage
        from frontend.core.registry import FeatureRegistry
        from frontend.core.router import Router, set_current_router
        from frontend.home.home_page import HomePage

        set_current_user(CurrentUser("u-admin", is_admin=True))
        set_current_router(Router(FeatureRegistry.discover(), HomePage(), CurrentUser("u-admin", is_admin=True)))
        AdminPage().run()

    page = AppTest.from_function(admin_page, default_timeout=60)
    page.run()
    assert not page.exception and not page.error, [e.value for e in [*page.exception, *page.error]]


def test_user_only_sees_granted_pages() -> None:
    AccessManager().ensure_admin()
    AccessManager().save_user(User(username="viewer", permissions=["sample_product_import/products"]), "pw")
    app = _login("viewer", "pw")
    assert "Quản trị" not in _menu_texts(app)
    links = _page_links(app)
    assert "Nhập sản phẩm từ Excel (mẫu)" in links  # a feature with one allowed page: a plain link to it
    assert "Nhập sản phẩm từ Excel" not in links and "Người dùng & phân quyền" not in links

"""Login screen, permission-filtered menu and the admin page, rendered with Streamlit's headless AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from backend.core.access import AccessManager, User, UserGroup
from backend.core.current_user import page_permission
from frontend.core.registry import FeatureRegistry

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


def _app_cards(app: AppTest) -> int:
    return sum(b.label == "Mở ứng dụng" for b in app.button)


def _sidebar_inside_app(username: str) -> AppTest:
    """The sidebar as the user sees it on the landing page of their first app."""

    def render(name: str) -> None:
        from backend.core.access import AccessManager
        from backend.core.current_user import set_current_user
        from frontend.core.components import render_sidebar_nav
        from frontend.core.registry import FeatureRegistry
        from frontend.core.router import Router, set_current_router
        from frontend.home.home_page import HomePage

        AccessManager().ensure_admin()
        user = AccessManager().refresh(name)
        assert user is not None, name  # a real user: the router filters by their rights
        set_current_user(user)
        router = Router(FeatureRegistry.discover(), HomePage(), user)
        set_current_router(router)
        router.navigation()
        render_sidebar_nav(router, router.landing_page(router.features[0].key))

    app = AppTest.from_function(render, args=(username,), default_timeout=60)
    app.run()
    assert not app.exception, [e.value for e in app.exception]
    return app


def test_wrong_password_stays_on_login() -> None:
    app = _login("u-admin", "wrong")
    assert any("Sai tên đăng nhập" in e.value for e in app.error)


def test_home_lists_the_apps_and_each_app_has_its_own_menu() -> None:
    app = _login("u-admin", "u-admin")
    manifests = FeatureRegistry.discover().visible_features()
    assert _page_links(app) == [], "Home: the sidebar shows only who is logged in, the apps are cards"
    assert _app_cards(app) == len(manifests)
    links = _page_links(_sidebar_inside_app("u-admin"))
    assert links == ["Tất cả ứng dụng", *(p.title for p in manifests[0].pages)]


def test_admin_page_is_reachable_by_url_only_and_renders() -> None:
    links = set(_page_links(_sidebar_inside_app("u-admin")))
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
    group = AccessManager().save_group(UserGroup(name="Sales"))
    AccessManager().save_user(User(username="an", group_ids=[group.id]), "pw")
    page.run()  # with a user and a group: both rights grids, the lists and the forms
    assert not page.exception and not page.error, [e.value for e in [*page.exception, *page.error]]
    assert [r.value for r in page.radio] == [None, None], "nothing is open until the admin clicks a name"
    page.radio[0].set_value(next(u.id for u in AccessManager().list_users() if u.username == "an")).run()
    assert not page.exception and "an" in [s.value for s in page.subheader]


def test_user_only_sees_granted_pages() -> None:
    AccessManager().ensure_admin()
    manifest = FeatureRegistry.discover().visible_features()[0]
    granted = manifest.pages[-1]
    AccessManager().save_user(User(username="viewer", permissions=[page_permission(manifest.key, granted.slug)]), "pw")
    app = _login("viewer", "pw")
    assert "Quản trị" not in _menu_texts(app)
    assert _app_cards(app) == 1, "only the app with a granted page is on Home"
    links = _page_links(_sidebar_inside_app("viewer"))
    assert links == ["Tất cả ứng dụng", granted.title], "inside the app: only the granted page"


def test_sample_feature_is_hidden_once_a_real_feature_exists() -> None:
    sample = FeatureRegistry.discover().get("sample_product_import")
    assert sample is not None and sample.sample
    real = sample.__class__(**{**sample.__dict__, "key": "real_feature", "sample": False})
    assert FeatureRegistry(features=[sample]).visible_features() == [sample]  # alone: shown as a demo
    assert FeatureRegistry(features=[sample, real]).visible_features() == [real]


def test_deferred_download_builds_on_click_as_the_user_who_clicked(monkeypatch) -> None:
    from concurrent.futures import ThreadPoolExecutor

    import streamlit as st

    from backend.core.base import FileDownloadDTO
    from backend.core.current_user import CurrentUser, get_current_user, set_current_user
    from frontend.core.components import download_button

    shown, built_by = {}, []
    monkeypatch.setattr(st, "download_button", lambda label, **kwargs: shown.update(kwargs))

    def build() -> FileDownloadDTO:
        built_by.append(get_current_user())
        return FileDownloadDTO(filename="x.xlsx", content=b"abc")

    clicker = CurrentUser("an")
    set_current_user(clicker)
    download_button(build, label="Xuất Excel", key="dl", file_name="bao-cao.xlsx")
    set_current_user(None)
    assert not built_by, "the file must not be built while the page renders"
    # Streamlit calls the function on its own thread when the user clicks
    assert ThreadPoolExecutor(1).submit(shown["data"]).result() == b"abc"
    assert built_by == [clicker]
    assert shown["file_name"] == "bao-cao.xlsx"

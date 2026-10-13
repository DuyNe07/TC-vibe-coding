"""SqlRepository (same API as the JSON repository) and the user / group permissions of backend.core.access."""

import pytest

from backend.core.access import ADMIN_USERNAME, AccessManager, User, UserGroup
from backend.core.base import BaseEntity, SqlRepository
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from backend.core.gateway import GatewayCall, PermissionMiddleware


class Note(BaseEntity):
    text: str
    tags: list[str] = []


class NoteRepository(SqlRepository[Note]):
    pass


def test_sql_repository_crud() -> None:
    repo = NoteRepository()
    assert repo.table.name == "core__note"
    first = repo.add(Note(text="a", tags=["x"]))
    with pytest.raises(ConflictError):
        repo.add(first)
    repo.save_many([Note(text="b"), Note(text="c")])
    assert repo.count() == 3
    first.text = "a2"
    repo.update(first)
    assert repo.get_or_raise(first.id).text == "a2"
    assert repo.find_one(lambda n: n.tags == ["x"]).id == first.id
    repo.delete(first.id)
    with pytest.raises(NotFoundError):
        repo.delete(first.id)
    assert sorted(n.text for n in repo.list_all()) == ["b", "c"]
    repo.clear()
    assert repo.count() == 0


def test_effective_permissions_are_personal_plus_groups() -> None:
    access = AccessManager()
    access.ensure_admin()
    admin = access.authenticate(ADMIN_USERNAME, "u-admin")
    assert admin is not None and admin.is_admin
    group = access.save_group(UserGroup(name="Sales", permissions=["yarn_costing/requests"]))
    access.save_user(User(username="an", permissions=["sample_product_import"], group_ids=[group.id]), "pw")
    user = access.authenticate("an", "pw")
    assert user is not None and user.permissions == {"sample_product_import", "yarn_costing/requests"}
    assert user.can_open_page("yarn_costing", "requests") and not user.can_open_page("yarn_costing", "main")
    assert user.can_open_feature("yarn_costing") and not user.can_open_feature("other_feature")
    assert access.authenticate("an", "wrong") is None


def test_built_in_admin_is_protected_and_only_admins_manage_users() -> None:
    access = AccessManager()
    access.ensure_admin()
    admin = next(u for u in access.list_users() if u.username == ADMIN_USERNAME)
    with pytest.raises(ConflictError):
        access.delete_user(admin.id)
    set_current_user(CurrentUser("an"))
    try:
        with pytest.raises(PermissionDeniedError):
            access.save_group(UserGroup(name="x"))
    finally:
        set_current_user(None)


def test_gateway_refuses_features_without_permission() -> None:
    call = GatewayCall("yarn_costing", None, "list", None)  # type: ignore[arg-type]
    middleware = PermissionMiddleware()
    set_current_user(CurrentUser("an", permissions=frozenset({"sample_product_import"})))
    try:
        with pytest.raises(PermissionDeniedError):
            middleware.handle(call, lambda c: "ok")
        set_current_user(CurrentUser("an", permissions=frozenset({"yarn_costing/requests"})))
        assert middleware.handle(call, lambda c: "ok") == "ok"
    finally:
        set_current_user(None)


def test_feature_tables_are_prefixed_with_the_developer() -> None:
    from backend.features.sample_product_import.repositories.product_repository import ProductRepository

    assert ProductRepository().table.name == "duyne07__sample_product_import__product"


def test_login_session_survives_reload_until_logout_or_expiry() -> None:
    from datetime import timedelta

    from backend.core.base import utc_now

    access = AccessManager()
    access.ensure_admin()
    token = access.start_session(ADMIN_USERNAME)
    resumed = access.resume(token)
    assert resumed is not None and resumed.username == ADMIN_USERNAME
    assert access.resume("forged-token") is None
    access.end_session(token)
    assert access.resume(token) is None
    expired = access.start_session(ADMIN_USERNAME)
    session = access.sessions.list_all()[0]
    session.expires_at = utc_now() - timedelta(minutes=1)
    access.sessions.update(session)
    assert access.resume(expired) is None

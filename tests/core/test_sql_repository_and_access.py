"""SqlRepository (same API as the JSON repository) and the user / group permissions of backend.core.access."""

import pytest

from backend.core.access import ADMIN_USERNAME, AccessManager, User, UserGroup
from backend.core.base import BaseEntity, SqlRepository
from backend.core.current_user import CurrentUser, role_permission, set_current_user
from backend.core.exceptions import ConflictError, InvalidInputError, NotFoundError, PermissionDeniedError
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


def test_rights_are_replaced_one_app_at_a_time() -> None:
    access = AccessManager()
    old = "removed_app/main"  # right of an app that no longer exists: kept untouched
    an = access.save_user(User(username="an", permissions=["yarn_costing", "sample_product_import/main", old]), "pw")
    binh = access.save_user(User(username="binh", permissions=["yarn_costing/requests"]), "pw")
    sales = access.save_group(UserGroup(name="Sales", permissions=["yarn_costing"]))
    an_rights = {"yarn_costing/requests", role_permission("yarn_costing", "SO")}
    changed = access.set_rights_in_app(
        "yarn_costing", {an.id: an_rights, binh.id: {"yarn_costing/requests"}}, {sales.id: set()}
    )
    assert changed == 2, "binh did not change, so only an + Sales are written"
    users = {u.username: u for u in access.list_users()}
    assert set(users["an"].permissions) == {*an_rights, "sample_product_import/main", old}
    logged_in = access.authenticate("an", "pw")
    assert logged_in is not None and logged_in.roles_in("yarn_costing") == {"SO"}
    assert logged_in.roles_in("sample_product_import") == set()
    assert access.list_groups()[0].permissions == []
    with pytest.raises(InvalidInputError):
        access.set_rights_in_app("yarn_costing", {an.id: {"sample_product_import"}}, {})
    access.set_group_members(sales.id, {binh.id})
    assert [u.username for u in access.list_users() if sales.id in u.group_ids] == ["binh"]
    set_current_user(CurrentUser("an"))
    try:
        with pytest.raises(PermissionDeniedError):
            access.set_rights_in_app("yarn_costing", {an.id: {"yarn_costing"}}, {})
    finally:
        set_current_user(None)


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


def test_user_changes_own_password_with_the_current_one() -> None:
    access = AccessManager()
    access.ensure_admin()
    access.save_user(User(username="an"), "pw")
    with pytest.raises(InvalidInputError):
        access.change_own_password("an", "wrong", "pw2")
    with pytest.raises(InvalidInputError):
        access.change_own_password("an", "pw", "")
    try:
        set_current_user(CurrentUser("binh", "", False, frozenset()))
        with pytest.raises(PermissionDeniedError):
            access.change_own_password("an", "pw", "pw2")
        set_current_user(CurrentUser("an", "", False, frozenset()))
        access.change_own_password("an", "pw", "pw2")
    finally:
        set_current_user(None)
    assert access.authenticate("an", "pw") is None and access.authenticate("an", "pw2") is not None


def test_warm_up_reads_every_repository_into_ram() -> None:
    from backend.core import db
    from frontend.core.warm_up import _preload, _repository_classes

    repo = NoteRepository()
    repo.add(Note(text="a"))
    db.table_changed(repo.table.name)  # as on a fresh server: nothing in RAM
    assert NoteRepository in _repository_classes()
    _preload(NoteRepository)
    cached = db.cached_table(repo.table.name)
    assert cached is not None and [n.text for n in cached.values()] == ["a"]


def test_reads_come_from_ram_until_this_process_writes() -> None:
    from backend.core import db
    from backend.core.base import BaseController, BaseRequestDTO, BaseResponseDTO, BaseService, cached_query
    from backend.core.gateway import gateway

    repo = NoteRepository()
    repo.add(Note(text="a"))
    assert [n.text for n in repo.list_all()] == ["a"]
    assert db.cached_table(repo.table.name) is not None  # second read: no database round trip

    class CountRequest(BaseRequestDTO):
        pass

    class CountResponse(BaseResponseDTO):
        count: int

    calls: list[int] = []

    class CountService(BaseService[CountRequest, CountResponse]):
        def execute(self, request: CountRequest) -> CountResponse:
            calls.append(1)
            return CountResponse(count=NoteRepository().count())

    class NotesController(BaseController):
        @cached_query
        def count_notes(self, request: CountRequest) -> CountResponse:
            return CountService().handle(request)

    notes = gateway.open(NotesController)
    assert notes.count_notes(CountRequest()).count == 1
    assert notes.count_notes(CountRequest()).count == 1 and len(calls) == 1  # served from RAM
    repo.add(Note(text="b"))  # any write invalidates
    assert notes.count_notes(CountRequest()).count == 2 and len(calls) == 2


def test_a_repository_that_seeds_on_first_read_does_not_recurse() -> None:
    class SeededRepository(SqlRepository[Note]):
        table_name = "core__seeded_note"

        def _load(self) -> dict[str, Note]:
            items = super()._load()
            if not items:
                seed = [Note(text="seed")]
                self.save_many(seed)  # save_many reads the stored rows: it must not call this _load again
                return {n.id: n for n in seed}
            return items

    assert [n.text for n in SeededRepository().list_all()] == ["seed"]
    assert SeededRepository().count() == 1


def test_master_manages_administrators_and_scopes_them() -> None:
    from backend.core.access import MASTER_USERNAME
    from backend.core.config import get_settings

    access = AccessManager()
    access.ensure_admin()
    admin = access.authenticate(ADMIN_USERNAME, "u-admin")
    assert admin is not None and admin.all_apps and not admin.admin_scoped, "no master yet: admins open everything"

    settings = get_settings()
    old, settings.master_password = settings.master_password, "m-secret"
    try:
        access.ensure_admin()
    finally:
        settings.master_password = old
    master = access.authenticate(MASTER_USERNAME, "m-secret")
    assert master is not None and master.is_master and master.is_admin and master.can_open_feature("any_app")
    admin = access.authenticate(ADMIN_USERNAME, "u-admin")
    assert admin is not None and admin.admin_scoped and not admin.can_open_feature("any_app")

    set_current_user(admin)
    try:
        with pytest.raises(PermissionDeniedError):  # an administrator can not create administrators
            access.save_user(User(username="boss", is_admin=True), "pw")
        with pytest.raises(PermissionDeniedError):  # nor rights in an app the master did not give them
            access.set_rights_in_app("any_app", {}, {})
        stored = access.users.by_username(ADMIN_USERNAME)
        access.save_user(stored.model_copy(update={"full_name": "Tôi"}), "new-pw")  # own profile: allowed
    finally:
        set_current_user(None)

    set_current_user(master)
    try:
        admin_user = access.users.by_username(ADMIN_USERNAME)
        assert access.set_rights_in_app("any_app", {admin_user.id: {"any_app"}}, {}) == 1
        with pytest.raises(ConflictError):
            access.delete_user(access.users.by_username(MASTER_USERNAME).id)
    finally:
        set_current_user(None)
    admin = access.authenticate(ADMIN_USERNAME, "new-pw")
    assert admin is not None and admin.can_open_feature("any_app") and not admin.can_open_feature("other_app")


def test_shared_database_rows_keep_the_format_older_app_versions_read() -> None:
    """Every machine uses ONE database: rows written by this version must never carry keys an older version rejects
    (its models forbid unknown keys), and this version must ignore keys written by a newer one."""
    from backend.core import db
    from backend.core.access import MASTER_USERNAME
    from backend.core.config import get_settings

    old_user = {"id", "created_at", "updated_at", "username", "full_name", "password_hash", "is_admin", "active",
                "group_ids", "permissions"}  # fmt: skip
    old_session = {"id", "created_at", "updated_at", "token_hash", "username", "expires_at"}
    access = AccessManager()
    settings = get_settings()
    old, settings.master_password = settings.master_password, "m-secret"
    try:
        access.ensure_admin()
    finally:
        settings.master_password = old
    token = access.start_session(MASTER_USERNAME)

    def documents(name: str) -> list[dict]:
        async def read() -> list[dict]:
            async with db.engine().connect() as connection:
                return [r.data for r in (await connection.execute(db.document_table(name).select())).all()]

        return db.run(read())

    assert all(set(d) <= old_user for d in documents("core__user")), documents("core__user")
    assert all(set(d) <= old_session for d in documents("core__session"))
    assert access.users.by_username(MASTER_USERNAME).is_master, "master = the u-master name, not a stored flag"
    access.end_session(token)
    assert documents("core__session") == [], "logout removes the technical session row (no flagged row left)"

    future = {**documents("core__user")[0], "added_by_a_newer_version": 1}

    async def write() -> None:
        async with db.engine().begin() as connection:
            table = db.document_table("core__user")
            await connection.execute(table.update().where(table.c.id == future["id"]).values(data=future))

    db.run(write())
    db.table_changed("core__user")
    assert access.users.get(future["id"]) is not None, "unknown keys from a newer version are ignored"

"""Admin page (/admin, administrators only, typed by hand).

Tab 1 - rights per app: pick an app, tick which screens each user / group may open (one grid like an Excel sheet).
Tab 2 - accounts, tab 3 - groups: a list on the left (one click opens it), the details on the right.
Effective rights of a user = personal rights + rights of all their groups. Administrators open everything.
"""

from collections.abc import Callable, Sequence
from typing import Any

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from backend.core.access import ADMIN_USERNAME, AccessManager, User, UserGroup
from backend.core.current_user import CurrentUser, in_app, page_permission, role_permission
from backend.core.exceptions import AppError, InvalidInputError
from frontend.core.base_page import BasePage
from frontend.core.components import editable_table, empty_state, section_title, show_error
from frontend.core.feature_manifest import FeatureManifest

WHOLE_APP = "Toàn bộ"
LONG_LIST = 8  # more items than this: a search box above the list


class AdminPage(BasePage):
    title = "Người dùng & phân quyền"
    icon = "🛡️"
    description = "Chọn ứng dụng rồi tick màn hình mỗi người được mở; quản lý tài khoản và nhóm người dùng."

    def __init__(self) -> None:
        super().__init__("admin")

    def render(self) -> None:
        if (flash := self.state.pop("flash")) is not None:
            st.toast(flash, icon=":material/check_circle:")
        access = AccessManager()
        users, groups = access.list_users(), access.list_groups()
        rights_tab, users_tab, groups_tab = st.tabs(["🔐 Quyền theo ứng dụng", "👤 Tài khoản", "👥 Nhóm"])
        with rights_tab:
            self._rights_tab(access, users, groups)
        with users_tab:
            self._users_tab(access, users, groups)
        with groups_tab:
            self._groups_tab(access, users, groups)

    # ---- rights per app ----
    def _rights_tab(self, access: AccessManager, users: list[User], groups: list[UserGroup]) -> None:
        from frontend.core.router import get_router

        apps = {m.key: m for m in get_router().registry.visible_features()}
        if not apps:
            empty_state("Chưa có ứng dụng nào để phân quyền.", icon="🧩")
            return
        app = apps[
            st.pills(
                "Ứng dụng",
                list(apps),
                format_func=lambda k: f"{apps[k].icon} {apps[k].title}",
                default=next(iter(apps)),
                required=True,
                key=self.key("app"),
            )  # fmt: skip
        ]
        pages = {page_permission(app.key, p.slug): p for p in app.pages}
        roles = {role_permission(app.key, code): label for code, label in app.roles}
        admins = [u.username for u in users if u.is_admin]
        st.caption(
            f"Tick ô để cho mở màn hình. **{WHOLE_APP}** = mọi màn hình của {app.title}, kể cả màn hình thêm sau này"
            + (" (không gồm vai trò; cột **Vai trò** do ứng dụng quyết định được làm gì). " if roles else ". ")
            + f"Quyền của nhóm được cộng cho mọi thành viên. Quản trị viên ({', '.join(admins)}) luôn mở được tất cả."
        )
        version = self.state.get("rights_version", 0)  # new grids after a save
        columns: dict[str, Any] = {
            "Tên đăng nhập": st.column_config.TextColumn(pinned=True),
            "Nhóm": st.column_config.TextColumn(pinned=True),
            "Có từ nhóm": st.column_config.TextColumn(help="Màn hình mở được nhờ nhóm (không sửa ở đây)"),
            WHOLE_APP: st.column_config.CheckboxColumn(WHOLE_APP, help="Mọi màn hình của ứng dụng"),
        }
        columns |= {k: st.column_config.CheckboxColumn(p.title, help=p.menu_group or None) for k, p in pages.items()}
        columns |= {k: st.column_config.CheckboxColumn(f"Vai trò {label}", help="Vai trò trong ứng dụng") for k, label in roles.items()}  # fmt: skip
        ticks = [*pages, *roles]

        user_rows: list[dict[str, Any]] = []
        group_rows: list[dict[str, Any]] = []
        people = [u for u in users if not u.is_admin]
        section_title("Người dùng")
        if people:
            keyword = self._search(len(people), "rights.search", "Tìm người dùng")
            group_rights = {g.id: {p for p in g.permissions if in_app(p, app.key)} for g in groups}
            user_rows = editable_table(
                [
                    {
                        "id": u.id,
                        "Tên đăng nhập": u.username,
                        "Họ tên": u.full_name,
                        "Có từ nhóm": self._summary(
                            app, pages, roles, set().union(*(group_rights.get(g, set()) for g in u.group_ids))
                        ),
                        **self._ticks(app.key, pages, roles, u.permissions),
                    }
                    for u in people
                    if self._found(keyword, u.username, u.full_name)
                ],
                key=self.key(f"rights.{app.key}.{version}.users.{keyword}"),
                columns=["id", "Tên đăng nhập", "Họ tên", "Có từ nhóm", WHOLE_APP, *ticks],
                column_order=["Tên đăng nhập", "Họ tên", "Có từ nhóm", WHOLE_APP, *ticks],
                column_config=columns,
                disabled=["Tên đăng nhập", "Họ tên", "Có từ nhóm"],
            )
        else:
            st.caption("Chưa có người dùng nào ngoài quản trị viên. Thêm ở thẻ 👤 Tài khoản.")
        section_title("Nhóm")
        if groups:
            group_rows = editable_table(
                [{"id": g.id, "Nhóm": g.name, **self._ticks(app.key, pages, roles, g.permissions)} for g in groups],
                key=self.key(f"rights.{app.key}.{version}.groups"),
                columns=["id", "Nhóm", WHOLE_APP, *ticks],
                column_order=["Nhóm", WHOLE_APP, *ticks],
                column_config=columns,
                disabled=["Nhóm"],
            )
        else:
            st.caption("Chưa có nhóm. Tạo nhóm ở thẻ 👥 Nhóm để cấp quyền cho nhiều người một lần.")
        if st.button(f"Lưu quyền {app.title}", type="primary", icon=":material/save:", key=self.key("rights.save")):

            def save() -> None:
                count = access.set_rights_in_app(
                    app.key,
                    self._wanted(app.key, pages, roles, user_rows),
                    self._wanted(app.key, pages, roles, group_rows),
                )
                self.state.set("rights_version", version + 1)
                self.state.set("flash", f"Đã lưu quyền {app.title}: {count} người / nhóm thay đổi.")

            self._run(save, None)

    @staticmethod
    def _ticks(
        app_key: str, pages: dict[str, Any], roles: dict[str, str], permissions: Sequence[str]
    ) -> dict[str, bool]:
        whole = app_key in permissions
        return {
            WHOLE_APP: whole,
            **{k: whole or k in permissions for k in pages},
            **{k: k in permissions for k in roles},
        }

    @staticmethod
    def _wanted(
        app_key: str, pages: dict[str, Any], roles: dict[str, str], rows: list[dict[str, Any]]
    ) -> dict[str, set[str]]:
        """Grid rows -> rights in the app: the whole app when ticked, otherwise the ticked screens; plus ticked roles."""
        return {
            r["id"]: ({app_key} if r[WHOLE_APP] else {k for k in pages if r[k]}) | {k for k in roles if r[k]}
            for r in rows
        }

    @staticmethod
    def _summary(app: FeatureManifest, pages: dict[str, Any], roles: dict[str, str], rights: set[str]) -> str:
        screens = [WHOLE_APP] if app.key in rights else [p.title for k, p in pages.items() if k in rights]
        return ", ".join([*screens, *(f"vai trò {label}" for k, label in roles.items() if k in rights)])

    # ---- accounts ----
    def _users_tab(self, access: AccessManager, users: list[User], groups: list[UserGroup]) -> None:
        group_names = {g.id: g.name for g in groups}
        left, right = st.columns([1, 2], gap="large")
        with left:
            if st.button("Thêm người dùng", icon=":material/person_add:", key=self.key("user.new"), width="stretch"):
                self._new_user_dialog(access, groups)
            picked = self._pick(
                "user", users,
                label=lambda u: (":material/shield_person: " if u.is_admin else "") + u.username
                + ("" if u.active else " :gray[(đã khoá)]"),
                caption=lambda u: ", ".join(filter(None, [u.full_name, *(group_names.get(g, "") for g in u.group_ids)])),
                search=lambda u: f"{u.username} {u.full_name}",
            )  # fmt: skip
        with right:
            user = next((u for u in users if u.id == picked), None)
            if user is None:
                st.info("Chọn một người dùng trong danh sách để xem và sửa.", icon=":material/arrow_back:")
                return
            self._user_form(access, user, groups)

    def _user_form(self, access: AccessManager, user: User, groups: list[UserGroup]) -> None:
        builtin = user.username == ADMIN_USERNAME
        with st.container(border=True), st.form(self.key(f"user.form.{user.id}"), border=False):
            st.subheader(user.username, anchor=False)
            left, right = st.columns(2)
            username = left.text_input("Tên đăng nhập", value=user.username, disabled=builtin)
            full_name = right.text_input("Họ tên", value=user.full_name)
            password = st.text_input("Mật khẩu mới", type="password", help="Để trống nếu không đổi mật khẩu.")
            left, right = st.columns(2)
            active = left.toggle("Đang hoạt động", value=user.active, disabled=builtin)
            is_admin = right.toggle("Quản trị (mở được tất cả)", value=user.is_admin, disabled=builtin)
            group_ids = self._groups_input(groups, user.group_ids)
            st.caption(self._apps_of(user, groups))
            saved = st.form_submit_button("Lưu thay đổi", type="primary", icon=":material/save:")
        if saved:
            values = {"username": username.strip(), "full_name": full_name.strip(), "active": active,
                      "is_admin": is_admin, "group_ids": group_ids}  # fmt: skip
            self._run(
                lambda: access.save_user(User.model_validate({**user.model_dump(), **values}), password),
                f"Đã lưu người dùng {username}.",
            )
        if not builtin and st.button("Xoá người dùng", icon=":material/delete:", key=self.key(f"user.del.{user.id}")):
            self._confirm_delete(f"người dùng **{user.username}**", lambda: access.delete_user(user.id), "user")

    def _new_user_dialog(self, access: AccessManager, groups: list[UserGroup]) -> None:
        @st.dialog("Thêm người dùng", icon=":material/person_add:")
        def dialog() -> None:
            with st.form(self.key("user.new.form"), border=False):
                username = st.text_input("Tên đăng nhập")
                full_name = st.text_input("Họ tên")
                password = st.text_input("Mật khẩu", type="password")
                group_ids = self._groups_input(groups, [])
                created = st.form_submit_button("Tạo người dùng", type="primary", icon=":material/person_add:")
            if created:

                def create() -> None:
                    user = User(username=username.strip(), full_name=full_name.strip(), group_ids=group_ids)
                    self.state.set("user.select", access.save_user(user, password).id)

                self._run(create, f"Đã tạo {username}. Cấp quyền ở thẻ 🔐 Quyền theo ứng dụng.")

        dialog()

    # ---- groups ----
    def _groups_tab(self, access: AccessManager, users: list[User], groups: list[UserGroup]) -> None:
        left, right = st.columns([1, 2], gap="large")
        with left:
            if st.button("Thêm nhóm", icon=":material/group_add:", key=self.key("group.new"), width="stretch"):
                self._new_group_dialog(access, users)
            picked = self._pick(
                "group", groups,
                label=lambda g: g.name,
                caption=lambda g: ", ".join(filter(None, [f"{sum(g.id in u.group_ids for u in users)} thành viên", g.description])),
                search=lambda g: f"{g.name} {g.description}",
            )  # fmt: skip
        with right:
            group = next((g for g in groups if g.id == picked), None)
            if group is None:
                if groups:
                    st.info("Chọn một nhóm trong danh sách để xem và sửa.", icon=":material/arrow_back:")
                else:
                    empty_state("Chưa có nhóm nào.", "Nhóm giúp cấp quyền cho nhiều người một lần.", icon="👥")
                return
            with st.container(border=True), st.form(self.key(f"group.form.{group.id}"), border=False):
                st.subheader(group.name, anchor=False)
                name = st.text_input("Tên nhóm", value=group.name)
                description = st.text_input("Mô tả", value=group.description)
                members = self._members_input(users, group)
                saved = st.form_submit_button("Lưu thay đổi", type="primary", icon=":material/save:")
            if saved:
                self._run(lambda: self._save_group(access, group, name, description, members), f"Đã lưu nhóm {name}.")
            if st.button("Xoá nhóm", icon=":material/delete:", key=self.key(f"group.del.{group.id}")):
                self._confirm_delete(f"nhóm **{group.name}**", lambda: access.delete_group(group.id), "group")

    def _new_group_dialog(self, access: AccessManager, users: list[User]) -> None:
        @st.dialog("Thêm nhóm", icon=":material/group_add:")
        def dialog() -> None:
            with st.form(self.key("group.new.form"), border=False):
                name = st.text_input("Tên nhóm", placeholder="Ví dụ: Phòng Kinh doanh")
                description = st.text_input("Mô tả")
                members = self._members_input(users, None)
                created = st.form_submit_button("Tạo nhóm", type="primary", icon=":material/group_add:")
            if created:
                self._run(lambda: self._save_group(access, None, name, description, members),
                          f"Đã tạo nhóm {name}. Cấp quyền ở thẻ 🔐 Quyền theo ứng dụng.")  # fmt: skip

        dialog()

    def _save_group(
        self, access: AccessManager, group: UserGroup | None, name: str, description: str, members: list[str]
    ) -> None:
        current = group.model_dump() if group else {}
        stored = access.save_group(
            UserGroup.model_validate({**current, "name": name.strip(), "description": description.strip()})
        )
        access.set_group_members(stored.id, set(members))
        self.state.set("group.select", stored.id)

    @staticmethod
    def _groups_input(groups: list[UserGroup], current: list[str]) -> list[str]:
        """Group picker; nothing is shown while no group exists (keeps the user's stale ids out)."""
        if not groups:
            return []
        return st.multiselect(
            "Thuộc nhóm",
            [g.id for g in groups],
            default=[g for g in current if any(x.id == g for x in groups)],
            format_func={g.id: g.name for g in groups}.get,
            placeholder="Chưa thuộc nhóm nào",
        )

    @staticmethod
    def _members_input(users: list[User], group: UserGroup | None) -> list[str]:
        return st.multiselect(
            "Thành viên",
            [u.id for u in users],
            default=[u.id for u in users if group and group.id in u.group_ids],
            format_func={u.id: f"{u.username} ({u.full_name})" if u.full_name else u.username for u in users}.get,
            placeholder="Chọn người dùng",
        )

    # ---- shared pieces ----
    def _pick(
        self,
        kind: str,
        items: Sequence[Any],
        *,
        label: Callable[[Any], str],
        caption: Callable[[Any], str],
        search: Callable[[Any], str],
    ) -> str | None:
        """Clickable list (one click = open). Returns the id of the open item."""
        key = self.key(f"{kind}.pick")
        if (pending := self.state.pop(f"{kind}.select")) is not None:  # set by a create / delete action
            st.session_state[key] = pending or None
        keyword = self._search(len(items), f"{kind}.search", "Tìm theo tên")
        current = st.session_state.get(key)
        shown = [i for i in items if i.id == current or self._found(keyword, search(i))]
        if not shown:
            st.caption("Không có kết quả." if items else "Danh sách trống.")
            return None
        by_id = {i.id: i for i in shown}
        with st.container(height=480 if len(shown) > LONG_LIST else "content"):
            return st.radio(
                "Danh sách",
                list(by_id),
                index=None,
                format_func=lambda i: label(by_id[i]),
                captions=[caption(i) for i in shown],
                key=key,
                label_visibility="collapsed",
            )

    def _search(self, count: int, name: str, placeholder: str) -> str:
        if count <= LONG_LIST:
            return ""
        return st.text_input(
            placeholder, key=self.key(name), placeholder=placeholder, icon=":material/search:",
            label_visibility="collapsed",
        ).strip()  # fmt: skip

    @staticmethod
    def _found(keyword: str, *texts: str) -> bool:
        return not keyword or keyword.lower() in " ".join(texts).lower()

    def _confirm_delete(self, what: str, action: Callable[[], None], kind: str) -> None:
        @st.dialog("Xác nhận xoá", icon=":material/delete:")
        def dialog() -> None:
            st.markdown(f"Xoá {what}? Thao tác này không hoàn tác được.")
            with st.container(horizontal=True):
                if st.button("Xoá", type="primary", icon=":material/delete:"):
                    self.state.set(f"{kind}.select", "")
                    self._run(action, "Đã xoá.")
                if st.button("Huỷ"):
                    st.rerun()

        dialog()

    @staticmethod
    def _apps_of(user: User, groups: list[UserGroup]) -> str:
        from frontend.core.router import get_router

        if user.is_admin:
            return "Được mở: mọi ứng dụng (quản trị)."
        rights = {*user.permissions, *(p for g in groups if g.id in user.group_ids for p in g.permissions)}
        who = CurrentUser(user.username, permissions=frozenset(rights))
        opened = []
        for m in get_router().registry.visible_features():
            if who.can_open_feature(m.key):
                roles = ", ".join(label for code, label in m.roles if code in who.roles_in(m.key))
                screens = f"{sum(who.can_open_page(m.key, p.slug) for p in m.pages)}/{len(m.pages)} màn hình"
                opened.append(f"{m.icon} {m.title} ({screens}{', vai trò ' + roles if roles else ''})")
        return "Được mở: " + (", ".join(opened) if opened else "chưa có ứng dụng nào.")

    def _run(self, action: Callable[[], Any], message: str | None) -> None:
        try:
            action()
        except AppError as exc:
            show_error(exc)
            return
        except PydanticValidationError as exc:
            show_error(InvalidInputError.from_pydantic(exc))
            return
        if message:
            self.state.set("flash", message)
        st.rerun()

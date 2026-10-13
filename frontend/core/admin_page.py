"""Admin page (/admin, administrators only): create accounts, groups, and grant features / pages.

Left: the list of users (or groups). Right: the selected one, with the features and pages it may open.
Effective rights of a user = personal rights + rights of all their groups.
"""

from typing import Any

import streamlit as st

from backend.core.access import ADMIN_USERNAME, AccessManager, User, UserGroup
from backend.core.current_user import page_permission
from backend.core.exceptions import AppError
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel, show_error, show_success

NEW = "__new__"


class AdminPage(BasePage):
    title = "Người dùng & phân quyền"
    icon = "🛡️"
    description = "Tạo tài khoản, nhóm người dùng và chọn chức năng / màn hình mỗi người được mở."

    def __init__(self) -> None:
        super().__init__("admin")

    def render(self) -> None:
        if (flash := self.state.pop("flash")) is not None:
            show_success(flash)
        access = AccessManager()
        users, groups = access.list_users(), access.list_groups()
        catalog = self._permission_catalog()
        users_tab, groups_tab = st.tabs(["👤 Người dùng", "👥 Nhóm người dùng"])
        with users_tab:
            self._users_tab(access, users, groups, catalog)
        with groups_tab:
            self._groups_tab(access, users, groups, catalog)

    # ---- users ----
    def _users_tab(self, access: AccessManager, users: list[User], groups: list[UserGroup], catalog: dict) -> None:
        group_names = {g.id: g.name for g in groups}
        left, right = st.columns([2, 3], gap="large")
        with left:
            if st.button("➕ Tạo người dùng mới", key=self.key("user.new"), width="stretch"):
                self.state.set("user", NEW)
            rows = [
                {
                    "id": u.id,
                    "Tên đăng nhập": u.username,
                    "Họ tên": u.full_name,
                    "Nhóm": ", ".join(group_names.get(g, "?") for g in u.group_ids),
                    "Quản trị": u.is_admin,
                    "Hoạt động": u.active,
                }
                for u in users
            ]
            picked = data_table(rows, column_order=list(rows[0])[1:] if rows else None, selection="single",
                                key=self.key("user.table"))  # fmt: skip
            if picked and self.state.get("user_pick") != picked[0]["id"]:
                self.state.set("user_pick", picked[0]["id"])
                self.state.set("user", picked[0]["id"])
        with right:
            selected = self.state.get("user")
            user = next((u for u in users if u.id == selected), None)
            if selected != NEW and user is None:
                st.info("Chọn một người dùng bên trái, hoặc bấm “Tạo người dùng mới”.", icon="👈")
                return
            self._user_form(access, user, groups, catalog)

    def _user_form(self, access: AccessManager, user: User | None, groups: list[UserGroup], catalog: dict) -> None:
        builtin = user is not None and user.username == ADMIN_USERNAME
        current: dict[str, Any] = user.model_dump() if user else {}
        with panel(f"Sửa: {user.username}" if user else "Người dùng mới", icon="👤"):
            with st.form(self.key(f"user.form.{user.id if user else NEW}")):
                username = st.text_input("Tên đăng nhập", value=current.get("username", ""), disabled=builtin)
                full_name = st.text_input("Họ tên", value=current.get("full_name", ""))
                password = st.text_input(
                    "Mật khẩu mới" if user else "Mật khẩu",
                    type="password",
                    help="Để trống nếu không đổi mật khẩu." if user else None,
                )
                c1, c2 = st.columns(2)
                active = c1.toggle("Đang hoạt động", value=current.get("active", True), disabled=builtin)
                is_admin = c2.toggle("Quản trị (toàn quyền)", value=current.get("is_admin", False), disabled=builtin)
                group_ids = st.multiselect(
                    "Thuộc nhóm",
                    [g.id for g in groups],
                    default=[g for g in current.get("group_ids", []) if any(x.id == g for x in groups)],
                    format_func={g.id: g.name for g in groups}.get,
                )
                permissions = self._permission_picker(catalog, current.get("permissions", []), "user")
                saved = st.form_submit_button("💾 Lưu", type="primary")
            if user:
                inherited = sorted({p for g in groups if g.id in user.group_ids for p in g.permissions})
                if inherited:
                    st.caption("Quyền nhận thêm từ nhóm: " + "; ".join(catalog.get(p, p) for p in inherited))
        if saved:
            values = {"username": username, "full_name": full_name, "active": active, "is_admin": is_admin,
                      "group_ids": group_ids, "permissions": permissions}  # fmt: skip
            self._run(
                lambda: access.save_user(User.model_validate({**current, **values}), password), "Đã lưu người dùng."
            )
        if user and not builtin and st.button("🗑️ Xoá người dùng", key=self.key(f"user.delete.{user.id}")):
            self.state.set("user", None)
            self._run(lambda: access.delete_user(user.id), f"Đã xoá người dùng {user.username}.")

    # ---- groups ----
    def _groups_tab(self, access: AccessManager, users: list[User], groups: list[UserGroup], catalog: dict) -> None:
        left, right = st.columns([2, 3], gap="large")
        with left:
            if st.button("➕ Tạo nhóm mới", key=self.key("group.new"), width="stretch"):
                self.state.set("group", NEW)
            rows = [
                {"id": g.id, "Nhóm": g.name, "Mô tả": g.description,
                 "Số thành viên": sum(g.id in u.group_ids for u in users)}
                for g in groups
            ]  # fmt: skip
            picked = data_table(rows, column_order=list(rows[0])[1:] if rows else None, selection="single",
                                key=self.key("group.table"), empty_message="Chưa có nhóm nào.")  # fmt: skip
            if picked and self.state.get("group_pick") != picked[0]["id"]:
                self.state.set("group_pick", picked[0]["id"])
                self.state.set("group", picked[0]["id"])
        with right:
            selected = self.state.get("group")
            group = next((g for g in groups if g.id == selected), None)
            if selected != NEW and group is None:
                st.info("Chọn một nhóm bên trái, hoặc bấm “Tạo nhóm mới”.", icon="👈")
                return
            current: dict[str, Any] = group.model_dump() if group else {}
            with (
                panel(f"Sửa nhóm: {group.name}" if group else "Nhóm mới", icon="👥"),
                st.form(self.key(f"group.form.{group.id if group else NEW}")),
            ):
                name = st.text_input("Tên nhóm", value=current.get("name", ""))
                description = st.text_input("Mô tả", value=current.get("description", ""))
                members = st.multiselect(
                    "Thành viên",
                    [u.id for u in users],
                    default=[u.id for u in users if group and group.id in u.group_ids],
                    format_func={u.id: f"{u.username} - {u.full_name}".strip(" -") for u in users}.get,
                )
                permissions = self._permission_picker(catalog, current.get("permissions", []), "group")
                saved = st.form_submit_button("💾 Lưu", type="primary")
            if saved:

                def save() -> None:
                    stored = access.save_group(
                        UserGroup.model_validate(
                            {**current, "name": name, "description": description, "permissions": permissions}
                        )
                    )
                    access.set_group_members(stored.id, set(members))
                    self.state.set("group", stored.id)

                self._run(save, "Đã lưu nhóm.")
            if group and st.button("🗑️ Xoá nhóm", key=self.key(f"group.delete.{group.id}")):
                self.state.set("group", None)
                self._run(lambda: access.delete_group(group.id), f"Đã xoá nhóm {group.name}.")

    # ---- helpers ----
    @staticmethod
    def _permission_catalog() -> dict[str, str]:
        """Every grantable key -> label: whole feature, then each of its pages."""
        from frontend.core.router import get_router

        catalog: dict[str, str] = {}
        for manifest in get_router().registry.visible_features():
            catalog[manifest.key] = f"{manifest.icon} {manifest.title} — toàn bộ"
            for page_cls in manifest.pages:
                group = f"[{page_cls.menu_group}] " if page_cls.menu_group else ""
                catalog[page_permission(manifest.key, page_cls.slug)] = f"{manifest.title} › {group}{page_cls.title}"
        return catalog

    def _permission_picker(self, catalog: dict[str, str], granted: list[str], scope: str) -> list[str]:
        options = [*catalog, *(p for p in granted if p not in catalog)]  # keep rights of removed features
        return st.multiselect(
            "Chức năng / màn hình được truy cập",
            options,
            default=granted,
            format_func=lambda key: catalog.get(key, f"{key} (không còn tồn tại)"),
            placeholder="Chọn chức năng hoặc từng màn hình",
            key=self.key(f"{scope}.permissions.{self.state.get(scope)}"),
        )

    def _run(self, action: Any, message: str) -> None:
        try:
            action()
        except AppError as exc:
            show_error(exc)
            return
        self.state.set("flash", message)
        st.rerun()

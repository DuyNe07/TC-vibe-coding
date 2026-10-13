"""Screen 8 (`nguoi-dung-nhat-ky`) - Người dùng & nhật ký (UC-01, UC-02)."""

from datetime import date, timedelta

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.audit_dto import ListAuditLogRequest
from backend.features.yarn_costing.dto.common_dto import ActorDTO
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from backend.features.yarn_costing.dto.user_dto import GroupMemberRowDTO, SaveUserGroupRequest, UserGroupDTO
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, editable_table, panel
from frontend.features.yarn_costing.components.actor_block import clear_actor, current_actor, render_actor_block
from frontend.features.yarn_costing.components.columns import count_col, datetime_col
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.display import yes_no
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.labels import ALL, all_or
from frontend.features.yarn_costing.components.permissions import action_state, explain

NAME_COL = "Tên"
ACTIVE_COL = "Còn hoạt động"


class UserAuditPage(BasePage):
    title = "Người dùng & nhật ký"
    menu_group = "Phòng SO"
    icon = "👥"
    slug = "nguoi-dung-nhat-ky"
    description = "Phòng SO khai báo nhóm người dùng, mã nội bộ và thành viên; mọi người xem nhật ký thay đổi."

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        actor = render_actor_block(feature, self.state, reference)
        show_flash(self.state)
        groups = reference.groups

        with panel("Nhóm người dùng", icon="👥"):
            picked = data_table(
                [
                    {
                        "Mã nhóm": g.code,
                        "Tên nhóm": g.name,
                        "Xưởng": g.factory_code or "-",
                        "Đang hoạt động": yes_no(g.active),
                        "Số thành viên": len(g.members),
                    }
                    for g in groups
                ],
                column_config={"Số thành viên": count_col("Số thành viên")},
                selection="single",
                key=self.key("groups"),
                empty_message="Chưa có nhóm người dùng.",
            )
        if picked:
            group = next((g for g in groups if g.code == picked[0]["Mã nhóm"]), None)
            if group is not None:
                self._edit_group(feature, actor, group)

        self._audit_log(feature, groups)

    def _edit_group(self, feature: YarnCostingController, actor: ActorDTO | None, g: UserGroupDTO) -> None:
        with panel(f"Nhóm {g.name}", icon="✏️"):
            c1, c2, c3 = st.columns([2, 2, 1], vertical_alignment="bottom")
            name = c1.text_input("Tên nhóm", value=g.name, max_chars=100, key=self.key(f"g_name.{g.code}"))
            new_code = c2.text_input(
                "Mã nội bộ mới",
                type="password",
                placeholder="Để trống = giữ mã cũ",
                max_chars=20,
                key=self.key(f"g_code.{g.code}"),
            )
            active = c3.toggle("Còn hoạt động", value=g.active, key=self.key(f"g_active.{g.code}"))
            st.caption("Mã nội bộ dài từ 4 đến 20 ký tự.")
            st.markdown("**Thành viên**")
            rows = editable_table(
                [{NAME_COL: m.name, ACTIVE_COL: m.active} for m in g.members],
                key=self.key(f"members.{g.code}"),
                columns=[NAME_COL, ACTIVE_COL],
                allow_add_delete=True,
                column_config={
                    NAME_COL: st.column_config.TextColumn(NAME_COL, max_chars=100, required=True),
                    ACTIVE_COL: st.column_config.CheckboxColumn(ACTIVE_COL, default=True),
                },
            )
            disabled, why = action_state(self.state, "UC-01")
            if st.button("Lưu nhóm", type="primary", key=self.key("g_save"), disabled=disabled, help=why):
                members = [
                    GroupMemberRowDTO(name=str(r[NAME_COL]).strip(), active=r.get(ACTIVE_COL) is not False)
                    for r in rows
                    if r.get(NAME_COL) and str(r[NAME_COL]).strip()
                ]
                changed_code = (new_code or "").strip() or None
                result = feature.save_user_group(
                    SaveUserGroupRequest(
                        actor=actor or ActorDTO(),
                        group_code=g.code,
                        name=name,
                        new_access_code=changed_code,
                        active=active,
                        members=members,
                    )
                )
                set_flash(self.state, result.message)
                info = current_actor(self.state)
                if changed_code and info and info["group_code"] == g.code:
                    clear_actor(self.state)
                    set_flash(self.state, "Mã nội bộ nhóm của bạn đã đổi, vui lòng xác thực lại.")
                st.session_state.pop(self.key(f"g_code.{g.code}"), None)
                st.rerun()
            explain(why)

    def _audit_log(self, feature: YarnCostingController, groups: list[UserGroupDTO]) -> None:
        names = {g.code: g.name for g in groups}
        today = date.today()
        with panel("Nhật ký thay đổi", icon="📜"):
            c1, c2, c3, c4 = st.columns(4)
            date_from = c1.date_input(
                "Từ ngày", value=today - timedelta(days=30), format="DD/MM/YYYY", key=self.key("log_from")
            )
            date_to = c2.date_input("Đến ngày", value=today, format="DD/MM/YYYY", key=self.key("log_to"))
            group = c3.selectbox(
                "Nhóm",
                [ALL, *names],
                format_func=lambda c: c if c == ALL else names.get(c, c),
                key=self.key("log_group"),
            )
            keyword = c4.text_input("Từ khoá", key=self.key("log_keyword"))
            log = feature.list_audit_log(
                ListAuditLogRequest(date_from=date_from, date_to=date_to, group_code=all_or(group), keyword=keyword)
            )
            items = sorted(log.items, key=lambda a: a.at, reverse=True)
            data_table(
                [
                    {
                        "Lúc": a.at,
                        "Nhóm": names.get(a.group_code, a.group_code),
                        "Người": a.person_name,
                        "Thao tác": a.action,
                        "Đối tượng": a.object_ref,
                        "Nội dung": a.detail,
                        "Lý do": a.reason,
                    }
                    for a in items
                ],
                column_config={"Lúc": datetime_col("Lúc")},
                empty_message="Chưa có nhật ký nào.",
                key=self.key("audit"),
            )

"""Screen 7 - Khách hàng: tìm, sửa, tải danh sách ban đầu (UC-12, UC-13, UC-35, UC-36)."""

import streamlit as st

from backend.core.current_user import get_current_user, set_current_user
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import CustomerTeam, RoleCode
from backend.features.woven_costing.dto.master_dto import (
    CustomerDTO,
    CustomerImportRequest,
    ListCustomersRequest,
    UpdateCustomerRequest,
)
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, file_upload, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash, show_flash
from frontend.features.woven_costing.components.labels import enum_values, text
from frontend.features.woven_costing.components.roles import has_any

PREVIEW = "cust.preview"


class CustomerPage(BasePage):
    title = "Khách hàng"
    icon = "👥"
    slug = "khach-hang"
    menu_group = "Phòng SO"
    description = "Danh sách khách hàng dùng trong costsheet: tìm, sửa, tải danh sách ban đầu."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        keyword = st.text_input(
            "Tìm kiếm", placeholder="Tên hoặc mã khách hàng", key=self.key("keyword"), persist_state="session"
        )
        data = feature.list_customers(ListCustomersRequest(keyword=(keyword or "").strip()))
        stat_row([("Khách hàng", format_number(len(data.rows)))])
        picked = data_table(
            [
                {
                    "id": c.id,
                    "Mã KH": c.customer_code,
                    "Tên": c.name,
                    "Team": text(c.team),
                    "Người tạo": c.created_by,
                    "Ngày tạo": c.created_at,
                    "Đang dùng": c.active,
                }
                for c in data.rows
            ],
            column_config={
                "Ngày tạo": st.column_config.DatetimeColumn("Ngày tạo", format="DD/MM/YYYY"),
                "Đang dùng": st.column_config.CheckboxColumn("Đang dùng"),
            },
            column_order=["Mã KH", "Tên", "Team", "Người tạo", "Ngày tạo", "Đang dùng"],
            selection="single",
            key=self.key("grid"),
            empty_message="Chưa có khách hàng.",
        )
        if not has_any(RoleCode.SO.value):
            return
        chosen = next((c for c in data.rows if picked and c.id == picked[0]["id"]), None)
        if st.button("Sửa", icon=":material/edit:", disabled=chosen is None, key=self.key("edit")) and chosen:
            self._edit_dialog(feature, chosen)
        self._import(feature)

    def _edit_dialog(self, feature: WovenCostingController, customer: CustomerDTO) -> None:
        user = get_current_user()
        teams = enum_values(CustomerTeam)

        @st.dialog("Sửa khách hàng", width="medium")
        def _dialog() -> None:
            set_current_user(user)
            key = self.key(f"edit.{customer.id}")
            name = st.text_input("Tên khách hàng", value=customer.name, max_chars=200, key=f"{key}.name")
            code = st.text_input("Mã khách hàng", value=customer.customer_code, max_chars=8, key=f"{key}.code")
            team = st.segmented_control("Team", teams, default=text(customer.team), required=True, key=f"{key}.team")
            active = st.toggle("Đang dùng", value=customer.active, key=f"{key}.active")
            if st.button("Lưu", type="primary", icon=":material/save:", key=f"{key}.save"):
                saved = attempt(
                    lambda: feature.update_customer(
                        UpdateCustomerRequest(
                            id=customer.id,
                            name=(name or "").strip(),
                            customer_code=(code or "").strip(),
                            team=team or text(customer.team),
                            active=active,
                        )
                    )
                )
                if saved is not None:
                    set_flash(self.state, saved.message)
                    st.rerun()

        _dialog()

    def _import(self, feature: WovenCostingController) -> None:
        expander = st.expander(
            "Tải danh sách khách hàng", icon=":material/upload_file:", key=self.key("import"), on_change="rerun"
        )
        with expander:
            if not expander.open:
                return
            file = file_upload(
                "File danh sách khách hàng (.xlsx)",
                types=[".xlsx", ".xls"],
                key=self.key("file"),
                help="Cột bắt buộc: Team, Customer; cột Mã KH không bắt buộc.",
            )
            preview = self.state.get(PREVIEW)
            if preview is not None and (file is None or preview[0] != file.filename):
                self.state.pop(PREVIEW)
                preview = None
            if st.button("Xem trước", icon=":material/preview:", disabled=file is None, key=self.key("preview")):
                result = attempt(lambda: feature.preview_customer_import(CustomerImportRequest(file=file)))
                if result is not None:
                    preview = (file.filename, result)
                    self.state.set(PREVIEW, preview)
            if preview is None or file is None:
                return
            p = preview[1]
            stat_row([("Sẽ thêm", format_number(p.added)), ("Bỏ qua (trùng)", format_number(p.skipped))])
            data_table(
                [{"Tên": r.name, "Mã KH": r.customer_code, "Team": r.team, "Kết quả": text(r.result)} for r in p.rows],
                empty_message="File không có dòng nào.",
            )
            if st.button(
                "Lưu", type="primary", icon=":material/save:", disabled=p.added == 0, key=self.key("import_save")
            ):
                saved = attempt(lambda: feature.save_customer_import(CustomerImportRequest(file=file)))
                if saved is not None:
                    self.state.pop(PREVIEW)
                    set_flash(self.state, saved.message)
                    st.rerun()

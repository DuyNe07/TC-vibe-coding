"""Screen 8 (`nguoi-dung-nhat-ky`) - Nhật ký thao tác (UC-02, BR-49)."""

from datetime import date, timedelta

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.audit_dto import ListAuditLogRequest
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel
from frontend.features.yarn_costing.components.columns import datetime_col
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.labels import ALL, all_or


class UserAuditPage(BasePage):
    title = "Nhật ký thao tác"
    menu_group = "Phòng SO"
    icon = "📜"
    slug = "nguoi-dung-nhat-ky"
    description = (
        "Xem ai đã làm gì và lúc nào: mọi thao tác làm thay đổi dữ liệu đều được ghi theo tài khoản đăng nhập."
    )

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        show_data_warnings(feature.get_reference_data(GetReferenceDataRequest(factory_code=None)))
        today = date.today()
        with panel("Nhật ký thao tác", icon="📜", description="Mới nhất ở trên cùng."):
            c1, c2, c3, c4, c5 = st.columns(5)
            date_from = c1.date_input(
                "Từ ngày", value=today - timedelta(days=30), format="DD/MM/YYYY", key=self.key("log_from")
            )
            date_to = c2.date_input("Đến ngày", value=today, format="DD/MM/YYYY", key=self.key("log_to"))
            in_range = feature.list_audit_log(ListAuditLogRequest(date_from=date_from, date_to=date_to))
            username = c3.selectbox("Tài khoản", [ALL, *in_range.usernames], key=self.key("log_user"))
            action = c4.selectbox("Thao tác", [ALL, *in_range.actions], key=self.key("log_action"))
            keyword = c5.text_input("Từ khoá", key=self.key("log_keyword"))
            filtered = username != ALL or action != ALL or bool(keyword.strip())
            log = (
                feature.list_audit_log(
                    ListAuditLogRequest(
                        date_from=date_from,
                        date_to=date_to,
                        username=all_or(username),
                        action=all_or(action),
                        keyword=keyword,
                    )
                )
                if filtered
                else in_range
            )
            data_table(
                [
                    {
                        "Lúc": a.at,
                        "Tài khoản": a.username,
                        "Họ tên": a.display_name,
                        "Thao tác": a.action,
                        "Đối tượng": a.object_ref,
                        "Nội dung": a.detail,
                        "Lý do": a.reason,
                    }
                    for a in log.items
                ],
                column_config={"Lúc": datetime_col("Lúc")},
                empty_message="Chưa có thao tác nào trong khoảng thời gian này.",
                key=self.key("audit"),
            )

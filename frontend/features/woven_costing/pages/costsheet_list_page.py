"""Screen 1 - Danh sách costsheet (landing page): lọc, xem, tạo mới, xuất Excel (UC-27, UC-28)."""

from datetime import date, timedelta
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import (
    CostsheetStatus,
    DyePlant,
    OrderType,
    PriceType,
    RoleCode,
)
from backend.features.woven_costing.dto.list_dto import ListCostsheetsRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.flash import show_flash
from frontend.features.woven_costing.components.labels import enum_values, num, status_column, text, to_pct
from frontend.features.woven_costing.components.navigation import new_costsheet, open_costsheet
from frontend.features.woven_costing.components.roles import has_any

RECENT_DAYS = 90
COLUMNS = {
    "Số costsheet": st.column_config.TextColumn("Số costsheet", pinned=True),
    "Phiên bản": st.column_config.NumberColumn("Phiên bản", format="v%d", width="small"),
    "Trạng thái": status_column(),
    "Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
    "Team": st.column_config.TextColumn("Team", width="small"),
    "Nhà máy nhuộm": st.column_config.TextColumn("Nhà máy nhuộm", width="small"),
    "Loại giá": st.column_config.TextColumn("Loại giá", width="small"),
    "Số mét": st.column_config.NumberColumn("Số mét", format="localized"),
    "Giá bán (VND/m)": st.column_config.NumberColumn("Giá bán (VND/m)", format="localized"),
    "Giá bán (USD/m)": st.column_config.NumberColumn("Giá bán (USD/m)", format="%.4f"),
    "Giá vốn (VND/m)": st.column_config.NumberColumn("Giá vốn (VND/m)", format="localized"),
    "F&I (VND/m)": st.column_config.NumberColumn("F&I (VND/m)", format="localized"),
    "GP%": st.column_config.NumberColumn("GP%", format="%.2f %%"),
    "OP%": st.column_config.NumberColumn("OP%", format="%.2f %%"),
    "Ngày duyệt": st.column_config.DatetimeColumn("Ngày duyệt", format="DD/MM/YYYY HH:mm"),
}
ORDER = [
    "Số costsheet", "Phiên bản", "Trạng thái", "Ngày tính giá", "Sales", "Team", "Khách hàng", "Thị trường",
    "Loại đơn", "OC", "Mã vải", "Hình thức bán", "Nhà máy nhuộm", "Loại giá", "Số mét", "Giá bán (VND/m)",
    "Giá bán (USD/m)", "Giá vốn (VND/m)", "F&I (VND/m)", "GP%", "OP%", "Cảnh báo", "Người duyệt", "Ngày duyệt",
]  # fmt: skip


class CostsheetListPage(BasePage):
    title = "Danh sách costsheet"
    icon = "📋"
    menu_group = "Sales"
    description = "Lọc, xem mọi costsheet được phép xem; tạo mới và xuất Excel."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        options = feature.get_costsheet_options(EmptyRequest())
        request = self._filters(options)
        data = feature.list_costsheets(request)
        k = data.kpis
        stat_row(
            [
                ("Số phiếu", format_number(k.total)),
                ("Chờ duyệt", format_number(k.pending)),
                ("Đã duyệt", format_number(k.approved)),
                ("Đã chốt đơn", format_number(k.closed)),
                ("Dưới ngưỡng GP/OP", format_number(k.below_threshold)),
                ("Độ co thấp / bằng 0", format_number(k.low_shrinkage)),
            ]
        )
        picked = data_table(
            [self._row(r) for r in data.rows],
            column_config=COLUMNS,
            column_order=ORDER,
            selection="single",
            key=self.key("grid"),
            empty_message="Chưa có costsheet nào phù hợp bộ lọc.",
        )
        can_create = has_any(RoleCode.SALES.value, RoleCode.TRUONG_TEAM.value, RoleCode.SO.value)
        with st.container(horizontal=True, gap="small"):
            create = st.button(
                "Tạo costsheet",
                type="primary",
                icon=":material/add:",
                key=self.key("new"),
                disabled=not can_create,
                help=None if can_create else "Chỉ Sales / Trưởng team / Phòng SO lập costsheet.",
            )
            open_ = st.button(
                "Mở phiếu đã chọn", icon=":material/folder_open:", key=self.key("open"), disabled=not picked
            )
            download_button(
                lambda: feature.export_costsheets(request),
                label="Xuất Excel",
                key=self.key("export"),
                file_name=f"danh-sach-costsheet-{date.today():%Y%m%d}.xlsx",
            )
        if create:
            new_costsheet(self)
        if open_ and picked:
            open_costsheet(self, str(picked[0]["id"]))

    def _filters(self, options: Any) -> ListCostsheetsRequest:
        today = date.today()
        with panel("Bộ lọc", icon="🔎"):
            c1, c2 = st.columns([2, 3])
            keyword = c1.text_input(
                "Từ khóa",
                placeholder="Số costsheet, mã vải, OC, style",
                key=self.key("keyword"),
                persist_state="session",
            )
            statuses = c2.multiselect(
                "Trạng thái",
                enum_values(CostsheetStatus),
                default=[s.value for s in CostsheetStatus if s != CostsheetStatus.DA_THAY_THE],
                key=self.key("statuses"),
                persist_state="session",
            )
            cols = st.columns(6)
            team = cols[0].selectbox(
                "Team", options.teams, index=None, placeholder="Tất cả", key=self.key("team"), persist_state="session"
            )
            users = {u.username: u.name for u in options.sales_users}
            sales = cols[1].selectbox(
                "Sales",
                list(users),
                index=None,
                format_func=lambda u: users.get(u, u),
                placeholder="Tất cả",
                key=self.key("sales"),
                persist_state="session",
            )
            customer = cols[2].selectbox(
                "Khách hàng",
                [c.name for c in options.customers],
                index=None,
                placeholder="Tất cả",
                key=self.key("customer"),
                persist_state="session",
            )
            selects: dict[str, Any] = {}
            for col, (name, label, enum_cls) in zip(
                cols[3:],
                (("dye_plant", "Nhà máy nhuộm", DyePlant), ("order_type", "Loại đơn", OrderType),
                 ("price_type", "Loại giá", PriceType)),
                strict=True,
            ):  # fmt: skip
                selects[name] = col.selectbox(
                    label,
                    enum_values(enum_cls),
                    index=None,
                    placeholder="Tất cả",
                    key=self.key(name),
                    persist_state="session",
                )
            c1, c2, c3 = st.columns([2, 1, 1], vertical_alignment="bottom")
            dates = c1.date_input(
                "Ngày tính giá (từ - đến)",
                value=(today - timedelta(days=RECENT_DAYS), today),
                format="DD/MM/YYYY",
                key=self.key("dates"),
                persist_state="session",
            )
            latest = c2.toggle("Chỉ phiên bản mới nhất", value=True, key=self.key("latest"), persist_state="session")
            below = c3.toggle("Chỉ dưới ngưỡng GP/OP", value=False, key=self.key("below"), persist_state="session")
        date_list = list(dates) if isinstance(dates, (tuple, list)) else [dates]
        date_from = date_list[0] if date_list else None
        date_to = date_list[1] if len(date_list) > 1 else date_from
        return ListCostsheetsRequest(
            keyword=(keyword or "").strip(),
            statuses=statuses,
            team=team,
            sales_username=sales,
            customer_name=customer,
            date_from=date_from,
            date_to=date_to,
            latest_only=latest,
            below_threshold_only=below,
            **selects,
        )

    @staticmethod
    def _row(r: Any) -> dict[str, Any]:
        return {
            "id": r.id,
            "Số costsheet": r.costsheet_no,
            "Phiên bản": r.version,
            "Trạng thái": [text(r.status)],
            "Ngày tính giá": r.costing_date,
            "Sales": r.sales_name,
            "Team": r.team,
            "Khách hàng": r.customer_name,
            "Thị trường": text(r.market),
            "Loại đơn": text(r.order_type),
            "OC": r.oc_no,
            "Mã vải": r.tcfno,
            "Hình thức bán": text(r.sale_form),
            "Nhà máy nhuộm": text(r.dye_plant),
            "Loại giá": text(r.price_type),
            "Số mét": num(r.order_meters),
            "Giá bán (VND/m)": num(r.sell_price_vnd),
            "Giá bán (USD/m)": num(r.sell_price_usd),
            "Giá vốn (VND/m)": num(r.cogs_vnd),
            "F&I (VND/m)": num(r.freight_insurance),
            "GP%": to_pct(r.gp_pct),
            "OP%": to_pct(r.op_pct),
            "Cảnh báo": r.warning_text,
            "Người duyệt": r.approved_by_name,
            "Ngày duyệt": r.approved_at,
        }

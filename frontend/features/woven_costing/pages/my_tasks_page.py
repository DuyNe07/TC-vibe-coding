"""Screen 3 - Việc chờ tôi: costsheets and data waiting for the user (UC-30)."""

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.list_dto import TaskGroupDTO
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, empty_state, panel, stat_row
from frontend.features.woven_costing.components.flash import show_flash
from frontend.features.woven_costing.components.labels import to_pct
from frontend.features.woven_costing.components.navigation import open_costsheet, open_job
from frontend.features.woven_costing.pages.exchange_rate_page import ExchangeRatePage
from frontend.features.woven_costing.pages.fabric_data_page import FabricDataPage

ICONS = {
    "approve": "📝",
    "returned": "↩️",
    "no_oc": "🏷️",
    "expired_prices": "⏰",
    "exchange_rate": "💱",
    "missing_yarn": "🧶",
    "job_approve": "🎨",
    "job_returned": "↩️",
}


class MyTasksPage(BasePage):
    title = "Việc chờ tôi"
    icon = "📥"
    slug = "viec-cho-toi"
    menu_group = "Sales"
    description = "Những costsheet và dữ liệu đang chờ bạn xử lý."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        data = feature.list_my_tasks(EmptyRequest())
        if data.groups:
            stat_row([(g.title, len(g.rows)) for g in data.groups])
        groups = [g for g in data.groups if g.rows]
        if not groups:
            empty_state("Không có việc nào đang chờ bạn.")
            return
        for group in groups:
            with panel(f"{group.title} ({len(group.rows)})", icon=ICONS.get(group.code, "📌")):
                if group.kind == "exchange_rate":
                    for row in group.rows:
                        st.warning(row.reason or group.title, icon="⚠️")
                    self.link_to(ExchangeRatePage, label="Đi tới Tỷ giá")
                elif group.kind == "dyeing_job":
                    self._jobs(group)
                elif group.kind == "fabric":
                    data_table([{"Mã vải": r.tcfno, "Lý do": r.reason} for r in group.rows])
                    self.link_to(FabricDataPage, label="Đi tới Dữ liệu mã vải")
                else:
                    self._costsheets(group)

    def _costsheets(self, group: TaskGroupDTO) -> None:
        picked = data_table(
            [
                {
                    "costsheet_id": r.costsheet_id,
                    "Số costsheet": r.costsheet_no,
                    "Phiên bản": r.version,
                    "Khách hàng": r.customer_name,
                    "Mã vải": r.tcfno,
                    "Sales": r.sales_name,
                    "Ngày tính giá": r.costing_date,
                    "GP%": to_pct(r.gp_pct),
                    "OP%": to_pct(r.op_pct),
                    "Lý do": r.reason,
                }
                for r in group.rows
            ],
            column_config={
                "Phiên bản": st.column_config.NumberColumn("Phiên bản", format="v%d", width="small"),
                "Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
                "GP%": st.column_config.NumberColumn("GP%", format="%.2f %%"),
                "OP%": st.column_config.NumberColumn("OP%", format="%.2f %%"),
            },
            column_order=[
                "Số costsheet",
                "Phiên bản",
                "Khách hàng",
                "Mã vải",
                "Sales",
                "Ngày tính giá",
                "GP%",
                "OP%",
                "Lý do",
            ],  # fmt: skip
            selection="single",
            key=self.key(f"grid.{group.code}"),
        )
        if st.button("Mở", icon=":material/folder_open:", key=self.key(f"open.{group.code}"), disabled=not picked):
            open_costsheet(self, str(picked[0]["costsheet_id"]))

    def _jobs(self, group: TaskGroupDTO) -> None:
        """2026-11-25: dyeing job orders waiting (Screen 8)."""
        picked = data_table(
            [{"id": r.costsheet_id, "Số phiếu": r.costsheet_no, "Khách hàng": r.customer_name, "Sales": r.sales_name,
              "Ngày tính giá": r.costing_date, "%GP": to_pct(r.gp_pct), "Lý do": r.reason} for r in group.rows],
            column_config={"Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
                           "%GP": st.column_config.NumberColumn("%GP", format="%.2f %%")},
            column_order=["Số phiếu", "Khách hàng", "Sales", "Ngày tính giá", "%GP", "Lý do"],
            selection="single",
            key=self.key(f"grid.{group.code}"),
        )  # fmt: skip
        if st.button("Mở", icon=":material/folder_open:", key=self.key(f"open.{group.code}"), disabled=not picked):
            open_job(self, str(picked[0]["id"]))

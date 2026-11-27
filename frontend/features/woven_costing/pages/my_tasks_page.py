"""Screen 3 - Việc chờ tôi: costsheets and data waiting for the user (UC-30).

2026-11-27: "Chờ tôi duyệt" shows every column a leader needs, approves many costsheets at once (UC-47) and returns one
from the table (UC-22); "Phiếu gia công chờ tôi duyệt" approves many job orders at once (UC-48)."""

from decimal import Decimal
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.costsheet_dto import CostsheetActionRequest
from backend.features.woven_costing.dto.list_dto import BulkApproveRequest, TaskGroupDTO, TaskRowDTO
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, empty_state, panel, stat_row
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.dialogs import confirm_dialog
from frontend.features.woven_costing.components.flash import show_flash
from frontend.features.woven_costing.components.labels import RED_FLAG, to_pct
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
                elif group.code == "approve":
                    self._approve_costsheets(feature, group)
                elif group.code == "job_approve":
                    self._approve_jobs(feature, group)
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

    # ---- 2026-11-27: approve from the table (UC-47, UC-48, UC-22) ------------------------------------------------
    def _approve_costsheets(self, feature: WovenCostingController, group: TaskGroupDTO) -> None:
        rows = {r.costsheet_id: r for r in group.rows}
        picked = data_table(
            [_approval_row(r) for r in group.rows],
            column_config=APPROVAL_CONFIG,
            column_order=APPROVAL_COLUMNS,
            selection="multi",
            key=self.key(f"grid.{group.code}"),
        )
        chosen = [rows[str(p["costsheet_id"])] for p in picked]
        st.caption(
            f"{RED_FLAG} GP% / OP% dưới ngưỡng. Tick nhiều phiếu để duyệt một lần; tick 1 phiếu để trả lại hoặc mở."
        )
        with st.container(horizontal=True, gap="small", vertical_alignment="bottom"):
            approve = st.button(
                f"Duyệt các phiếu đã chọn ({len(chosen)})" if chosen else "Duyệt các phiếu đã chọn",
                type="primary", icon=":material/done_all:", key=self.key("approve_many"), disabled=not chosen,
            )  # fmt: skip
            one = chosen[0] if len(chosen) == 1 else None
            reason = st.text_input("Lý do trả lại", max_chars=500, key=self.key("return_reason"), disabled=one is None)
            give_back = st.button("Trả lại", icon=":material/undo:", key=self.key("return_one"), disabled=one is None)
            if st.button("Mở", icon=":material/folder_open:", key=self.key("open.approve"), disabled=one is None):
                open_costsheet(self, str(one.costsheet_id) if one else "")
        if approve:
            self._confirm_many(
                "costsheets", "Duyệt costsheet", chosen, lambda: feature.approve_costsheets(_ids(chosen)),
                [f"{r.costsheet_no} v{r.version}: GP% {_pct(r.gp_pct)}, OP% {_pct(r.op_pct)}" for r in chosen],
            )  # fmt: skip
        if give_back and one is not None:
            if not (reason or "").strip():
                st.error("Vui lòng nhập lý do trả lại.", icon="⛔")
            else:
                label = f"{one.costsheet_no} v{one.version}"
                confirm_dialog(
                    self.state, self.key("return_dialog"), "Trả lại costsheet",
                    f"Trả lại costsheet {label} cho người lập? Lý do: {reason.strip()}", "Trả lại",
                    lambda _: (feature.return_costsheet(CostsheetActionRequest(
                        costsheet_id=str(one.costsheet_id), reason=reason.strip())).message, ()),
                )  # fmt: skip

    def _approve_jobs(self, feature: WovenCostingController, group: TaskGroupDTO) -> None:
        rows = {r.costsheet_id: r for r in group.rows}
        picked = data_table(
            [_job_approval_row(r) for r in group.rows],
            column_config=JOB_CONFIG,
            column_order=JOB_COLUMNS,
            selection="multi",
            key=self.key(f"grid.{group.code}"),
        )
        chosen = [rows[str(p["id"])] for p in picked]
        with st.container(horizontal=True, gap="small"):
            approve = st.button(
                f"Duyệt các phiếu đã chọn ({len(chosen)})" if chosen else "Duyệt các phiếu đã chọn",
                type="primary", icon=":material/done_all:", key=self.key("approve_jobs"), disabled=not chosen,
            )  # fmt: skip
            one = chosen[0] if len(chosen) == 1 else None
            if st.button("Mở", icon=":material/folder_open:", key=self.key("open.job_approve"), disabled=one is None):
                open_job(self, str(one.costsheet_id) if one else "")
        if approve:
            self._confirm_many(
                "jobs", "Duyệt phiếu gia công", chosen, lambda: feature.approve_dyeing_jobs(_ids(chosen)),
                [f"{r.costsheet_no}: %GP {_pct(r.gp_pct)}" for r in chosen],
            )  # fmt: skip

    def _confirm_many(self, what: str, title: str, chosen: list[TaskRowDTO], call: Any, lines: list[str]) -> None:
        """Hộp xác nhận: the ticked orders with their margins; those with "Cần chú ý" listed apart (BR-102)."""
        notes = [
            f"{r.costsheet_no}{f' v{r.version}' if r.version else ''}: {r.attention}" for r in chosen if r.attention
        ]
        question = f"Duyệt {len(chosen)} phiếu?\n\n" + "\n".join(f"- {line}" for line in lines)
        if notes:
            question += "\n\nCác phiếu cần chú ý (vẫn duyệt được):"

        def action(_: str | None) -> tuple[str, list[str]]:
            result = call()
            return result.message, list(result.failed)

        confirm_dialog(self.state, self.key(f"approve_dialog.{what}"), title, question, "Duyệt", action, notes=notes)


def _ids(rows: list[TaskRowDTO]) -> BulkApproveRequest:
    return BulkApproveRequest(ids=[str(r.costsheet_id) for r in rows])


def _pct(value: Decimal | None) -> str:
    return "-" if value is None else f"{format_number(value * 100, 2)}%"


def _flag(value: Decimal | None, below: bool) -> str:
    return f"{RED_FLAG} {_pct(value)}" if below else _pct(value)


def _money(value: Decimal | None, currency: str | None) -> str:
    if value is None:
        return ""
    return f"{format_number(value, 0 if currency == 'VND' else 4)} {currency or ''}/m".strip()


def _approval_row(r: TaskRowDTO) -> dict[str, Any]:
    """Screen 3 "Chờ tôi duyệt" columns (2026-11-27), in the order of the document."""
    before_after = ""
    if r.prev_sell_price is not None:
        before_after = (
            f"{_money(r.prev_sell_price, r.sell_currency).split(' ')[0]} → {_money(r.sell_price, r.sell_currency)}"
        )
    gp_change = f"{_pct(r.prev_gp_pct)} → {_pct(r.gp_pct)}" if r.prev_gp_pct is not None else ""
    return {
        "costsheet_id": r.costsheet_id,
        "Số costsheet": r.costsheet_no,
        "Phiên bản": r.version,
        "Team": r.team,
        "Sales": r.sales_name,
        "Khách hàng": r.customer_name,
        "Mã vải": r.tcfno,
        "Tên vải": r.fabric_name,
        "Thị trường": r.market,
        "Nhà máy nhuộm": r.dye_plant,
        "Hình thức bán": r.sale_form,
        "Loại đơn": r.order_type,
        "Loại giá": r.price_type,
        "Số lượng đặt (m)": r.order_meters,
        "Ngày tính giá": r.costing_date,
        "Ngày gửi duyệt": r.submitted_at,
        "Ngày giao hàng": r.delivery_date,
        "Giá bán": _money(r.sell_price, r.sell_currency),
        "Giá vốn (đ/m)": r.cogs_vnd,
        "GP (đ/m)": r.gp_vnd,
        "GP%": _flag(r.gp_pct, r.gp_below),
        "OP%": _flag(r.op_pct, r.op_below),
        "Giá có VAT": r.price_with_vat,
        "Tiền sợi (đ/m)": r.yarn_per_m,
        "Tiền Dệt (đ/m)": r.weaving_per_m,
        "Tiền Nhuộm (đ/m)": r.dyeing_per_m,
        "Độ co (%)": to_pct(r.shrinkage),
        "Giá bán trước → nay": before_after,
        "GP% trước → nay": gp_change,
        "Cần chú ý": r.attention,
        "Ghi chú của Sales": r.note,
    }


def _job_approval_row(r: TaskRowDTO) -> dict[str, Any]:
    return {
        "id": r.costsheet_id,
        "Số phiếu": r.costsheet_no,
        "Khách hàng": r.customer_name,
        "Số hợp đồng": r.contract_no,
        "Đơn vị gia công": r.dye_plant,
        "Sales": r.sales_name,
        "Ngày tính giá": r.costing_date,
        "Tổng số lượng (m)": r.total_quantity,
        "Tổng giá GC (đ)": r.total_revenue,
        "%GP": _flag(r.gp_pct, r.gp_below),
        "Cần chú ý": r.attention,
    }


APPROVAL_COLUMNS = [k for k in _approval_row(TaskRowDTO()) if k != "costsheet_id"]
APPROVAL_CONFIG = {
    "Số costsheet": st.column_config.TextColumn("Số costsheet", pinned=True),
    "Phiên bản": st.column_config.NumberColumn("Phiên bản", format="v%d", width="small"),
    "Số lượng đặt (m)": st.column_config.NumberColumn("Số lượng đặt (m)", format="localized"),
    "Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
    "Ngày gửi duyệt": st.column_config.DatetimeColumn("Ngày gửi duyệt", format="DD/MM/YYYY HH:mm"),
    "Ngày giao hàng": st.column_config.DateColumn("Ngày giao hàng", format="DD/MM/YYYY"),
    **{c: st.column_config.NumberColumn(c, format="localized") for c in (
        "Giá vốn (đ/m)", "GP (đ/m)", "Giá có VAT", "Tiền sợi (đ/m)", "Tiền Dệt (đ/m)", "Tiền Nhuộm (đ/m)")},
    "Độ co (%)": st.column_config.NumberColumn("Độ co (%)", format="%.2f %%"),
    "Cần chú ý": st.column_config.TextColumn("Cần chú ý", width="large"),
}  # fmt: skip
JOB_COLUMNS = [k for k in _job_approval_row(TaskRowDTO()) if k != "id"]
JOB_CONFIG = {
    "Ngày tính giá": st.column_config.DateColumn("Ngày tính giá", format="DD/MM/YYYY"),
    "Tổng số lượng (m)": st.column_config.NumberColumn("Tổng số lượng (m)", format="localized"),
    "Tổng giá GC (đ)": st.column_config.NumberColumn("Tổng giá GC (đ)", format="localized"),
    "Cần chú ý": st.column_config.TextColumn("Cần chú ý", width="large"),
}

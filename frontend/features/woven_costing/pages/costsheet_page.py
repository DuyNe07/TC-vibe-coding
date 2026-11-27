"""Screen 2 - Costsheet: lập, tính, xem và duyệt một costsheet (UC-14..UC-26, UC-29)."""

import hashlib
from datetime import date, timedelta
from typing import Any

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import (
    CostsheetAction,
    CostsheetStatus,
    RoleCode,
    SaleForm,
    WarningSection,
)
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, GetCostsheetRequest
from backend.features.woven_costing.dto.list_dto import CostsheetOptionsResponse, ListCostsheetsRequest
from frontend.core.base_page import BasePage
from frontend.core.formatting import format_datetime, format_number
from frontend.features.woven_costing.components.costsheet_chain import (
    demand_chain_tab,
    section_warnings,
    show_warnings,
)
from frontend.features.woven_costing.components.costsheet_dyeing import dyeing_tab
from frontend.features.woven_costing.components.costsheet_order import create_panel, order_block
from frontend.features.woven_costing.components.costsheet_price import price_tab
from frontend.features.woven_costing.components.costsheet_request import build_input_request
from frontend.features.woven_costing.components.costsheet_tabs import (
    fabric_tab,
    history_tab,
    params_tab,
    warnings_tab,
    yarn_tab,
)
from frontend.features.woven_costing.components.costsheet_toolbar import toolbar
from frontend.features.woven_costing.components.costsheet_weaving import weaving_tab
from frontend.features.woven_costing.components.errors import attempt, show_error_list
from frontend.features.woven_costing.components.flash import show_flash
from frontend.features.woven_costing.components.labels import pct_text, status_badge, text
from frontend.features.woven_costing.components.marks import guide, tab_label
from frontend.features.woven_costing.components.working import (
    OPEN_ID,
    REV,
    WORKING,
    needs_calculation,
    open_id,
    replace_working,
)

RECENT_DAYS = 90
MAX_PICKER_ITEMS = 200
# tab names (the 5 business tabs are named like the warning sections they show)
PRICE = WarningSection.PRICE.value
FABRIC = WarningSection.FABRIC.value
DYEING = WarningSection.DYEING.value
WEAVING = WarningSection.WEAVING.value
YARN = WarningSection.YARN.value
PARAMS = "Tham số"
WARNINGS = "Cảnh báo"
HISTORY = "Lịch sử"
CHAIN = "Chuỗi nhu cầu"  # a tab since 2026-11-27 (before: a block above the tabs)
INPUT_TABS = (PRICE, DYEING, WEAVING, YARN, PARAMS)  # tabs with cells to type in: ✏️ on an editable costsheet


class CostsheetPage(BasePage):
    title = "Costsheet"
    icon = "🧾"
    slug = "costsheet"
    menu_group = "Sales"
    description = "Lập, tính, xem và duyệt một costsheet."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        options = feature.get_costsheet_options(EmptyRequest())
        working = self._working(feature)
        self._picker(feature, options, working)
        if working is None:
            create_panel(self, feature, options)
            return
        sfx = f"{working.id}.{self.state.get(REV, 0)}"
        self._header(working)
        self._summary(working)
        guide(working.editable)  # UI change 2026-11-27
        values: dict[str, Any] = {"order": order_block(self, feature, working, options, sfx)}
        values |= self._tabs(working, options, sfx, values["order"])
        st.space("small")
        if not toolbar(self, feature, working, values):
            self._auto_calculate(feature, working, values)

    # ---- UC-16 auto-calculation (2026-11-23: no "Tính lại" button) ----------------------------------------------
    def _auto_calculate(self, feature: WovenCostingController, w: CostsheetResponse, values: dict[str, Any]) -> None:
        """Like Excel: when a cell differs from the cells shown with the current results, recalculate (not saved) and
        draw the page again with the new results; read-only costsheets are never recalculated."""
        if not w.editable or CostsheetAction.RECALCULATE not in w.allowed_actions:
            return
        request = build_input_request(w, values)
        fingerprint = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        if not needs_calculation(self.state, w.id, fingerprint):
            return
        response = attempt(lambda: feature.calculate_costsheet(request))
        if response is not None:
            replace_working(self.state, response, dirty=True)
            st.rerun()

    # ---- loading ------------------------------------------------------------------------------------------------
    def _working(self, feature: WovenCostingController) -> CostsheetResponse | None:
        """The costsheet being worked on: loaded once when opened, then kept in the session (inputs survive reruns)."""
        cid = self.state.get(OPEN_ID)
        if not cid:
            return None
        working = self.state.get(WORKING)
        if working is not None and working.id == cid:
            return working
        try:
            working = feature.get_costsheet(GetCostsheetRequest(costsheet_id=cid))
        except AppError as exc:
            show_error_list(exc)
            open_id(self.state, None)
            return None
        replace_working(self.state, working)
        return working

    def _picker(
        self, feature: WovenCostingController, options: CostsheetOptionsResponse, w: CostsheetResponse | None
    ) -> None:
        """Box "Phiếu đang mở": type or pick a costsheet number (+ version), open it, or start a new one."""
        today = date.today()
        recent = feature.list_costsheets(
            ListCostsheetsRequest(latest_only=True, date_from=today - timedelta(days=RECENT_DAYS), date_to=today)
        )
        numbers = list(dict.fromkeys(r.costsheet_no for r in recent.rows))[:MAX_PICKER_ITEMS]
        current = w.costsheet_no if w else None
        if current and current not in numbers:
            numbers.insert(0, current)
        with st.container(horizontal=True, gap="small", vertical_alignment="bottom"):
            number = st.selectbox(
                "Phiếu đang mở",
                numbers,
                index=numbers.index(current) if current else None,
                accept_new_options=True,
                placeholder="Gõ hoặc chọn số costsheet",
                key=self.key(f"pick_no.{current or 'new'}"),
            )
            version = None
            if w is not None:
                versions = [v.version for v in w.versions] or [w.version]
                version = st.selectbox(
                    "Phiên bản",
                    versions,
                    index=versions.index(w.version) if w.version in versions else 0,
                    format_func=lambda v: f"v{v}",
                    key=self.key(f"pick_ver.{w.id}"),
                )
            go = st.button("Mở", icon=":material/folder_open:", key=self.key("pick_go"), disabled=not number)
            creators = {RoleCode.SALES.value, RoleCode.TRUONG_TEAM.value, RoleCode.SO.value}
            new = w is not None and set(options.my_roles) & creators
            if new and st.button("Tạo costsheet mới", icon=":material/add:", key=self.key("pick_new")):
                open_id(self.state, None)
                st.rerun()
        if go and number:
            no = str(number).strip().upper()
            wanted = version if w is not None and no == w.costsheet_no else None
            opened = attempt(lambda: feature.get_costsheet(GetCostsheetRequest(costsheet_no=no, version=wanted)))
            if opened is not None:
                replace_working(self.state, opened)
                st.rerun()

    # ---- header -------------------------------------------------------------------------------------------------
    def _header(self, w: CostsheetResponse) -> None:
        with st.container(horizontal=True, gap="small", vertical_alignment="center"):
            st.markdown(f"### {w.costsheet_no} · v{w.version}")
            status_badge(w.status)
            if w.fabric_overridden:
                st.badge("Thông số vải đã sửa", color="orange", icon=":material/edit:")
            if w.auto_approved:
                st.badge("Duyệt tự động", color="green", icon=":material/bolt:")
        parts = [
            f"Người lập: {w.sales_name or '-'} ({w.team or '-'})",
            f"Người duyệt: {w.approved_by_name or '-'} {format_datetime(w.approved_at) if w.approved_at else ''}".strip(),
            f"Tỷ giá {format_number(w.exchange_rate)}",
            f"Bộ định mức {w.norm_set_code or '-'}",
            f"Bộ tham số {w.parameter_set_date:%d/%m/%Y}" if w.parameter_set_date else "Bộ tham số -",
        ]
        if w.copied_from:
            parts.append(f"Sao chép từ {w.copied_from}")
        st.caption(" · ".join(parts))
        status = text(w.status)
        if w.return_reason:
            st.warning(f"Lý do trả lại: {w.return_reason}", icon=":material/undo:")
        if status == CostsheetStatus.HUY.value:
            st.error(f"Đã hủy. Lý do: {w.cancel_reason or '-'}", icon=":material/block:")
        elif not w.editable:
            st.info(f"Phiếu đang ở trạng thái {status}, chỉ xem.", icon=":material/visibility:")

    def _summary(self, w: CostsheetResponse) -> None:
        r = w.result
        cols = st.columns(5)
        if not r.calculated:
            for col, label in zip(cols, ("Đơn giá (đ/m)", "Giá vốn", "Giá bán", "GP%", "OP%"), strict=True):
                col.metric(label, "-", border=True)
            return
        cols[0].metric("Đơn giá (đ/m)", format_number(r.unit_cost_vnd), border=True)
        cols[1].metric("Giá vốn", format_number(r.cogs_vnd), border=True)
        cols[2].metric("Giá bán", format_number(r.sell_price_vnd), border=True)
        for col, label, value, threshold in (
            (cols[3], "GP%", r.gp_pct, r.gp_threshold),
            (cols[4], "OP%", r.op_pct, r.op_threshold),
        ):
            col.metric(
                label,
                pct_text(value),
                delta=f"{pct_text(value - threshold)} so với ngưỡng {pct_text(threshold)}",
                delta_color="normal",
                border=True,
            )

    # ---- tabs ---------------------------------------------------------------------------------------------------
    def _tabs(
        self, w: CostsheetResponse, options: CostsheetOptionsResponse, sfx: str, order: dict[str, Any]
    ) -> dict[str, Any]:
        """Every tab is drawn on each run (not lazy) so edited cells survive tab switches and the action bar reads all.

        Order (UI change 2026-11-23): Giá bán & lợi nhuận, Thông số vải, Nhuộm (not Mộc), Ngành Dệt and Sợi (not Vải
        Nhuộm), Tham số, Cảnh báo, Lịch sử. A tab with warnings shows them at its top and their count in its label;
        the key does not depend on the labels, so typed cells are kept when a count changes.

        UI change 2026-11-27: "Chuỗi nhu cầu" is the 2nd tab; tabs with cells to type in carry ✏️ while the costsheet
        can be edited."""
        sale_form = order.get("sale_form")
        with_dyeing = sale_form not in (SaleForm.GREIGE.value, SaleForm.WEAVING_JOB.value)  # BR-89 (2026-11-25)
        with_weaving = sale_form not in (SaleForm.DYED.value, SaleForm.DYEING_JOB.value)  # BR-90 (2026-11-25)
        names = [PRICE, CHAIN, FABRIC]
        names += [DYEING] if with_dyeing else []
        names += [WEAVING, YARN] if with_weaving else []
        names += [PARAMS, WARNINGS, HISTORY]
        own = {name: section_warnings(w.warnings, name) for name in names}
        own[WARNINGS] = w.warnings
        labels = [
            tab_label(name, editable=w.editable and name in INPUT_TABS, warnings=len(own[name])) for name in names
        ]
        layout = f"{int(with_dyeing)}{int(with_weaving)}"
        tabs = dict(zip(names, st.tabs(labels, key=self.key(f"tabs.{w.id}.{layout}")), strict=True))
        values: dict[str, Any] = {}
        with tabs[PRICE]:
            show_warnings(own[PRICE])
            values["price"] = price_tab(self, w, sfx, order.get("price_type"))
        with tabs[CHAIN]:
            demand_chain_tab(w)
        with tabs[FABRIC]:
            show_warnings(own[FABRIC])
            fabric_tab(w)
        if with_dyeing:
            with tabs[DYEING]:
                show_warnings(own[DYEING])
                values["hcm_dyeing"], values["tcdn_dyeing"] = dyeing_tab(self, w, options, sfx, order.get("dye_plant"))
        if with_weaving:
            with tabs[WEAVING]:
                show_warnings(own[WEAVING])
                values["twist_lines"], values["weaving"] = weaving_tab(self, w, options, sfx, sale_form)
            with tabs[YARN]:
                show_warnings(own[YARN])
                if sale_form == SaleForm.WEAVING_JOB.value:
                    st.info(
                        "Gia công dệt: khách giao sợi, không tính tiền sợi. Cột lượng sợi là số kg khách cần giao; "
                        "giá sợi không bắt buộc.",
                        icon=":material/info:",
                    )
                values["yarn_lines"] = yarn_tab(self, w, sfx)
        with tabs[PARAMS]:
            values["parameter_overrides"] = params_tab(self, w, sfx)
        with tabs[WARNINGS]:
            warnings_tab(w)
        with tabs[HISTORY]:
            version_id = history_tab(self, w)
        if version_id:
            open_id(self.state, version_id)
            st.rerun()
        return values

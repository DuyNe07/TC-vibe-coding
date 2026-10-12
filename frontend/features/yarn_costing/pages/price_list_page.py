"""Screen 1 (landing) - Bảng giá đã tính (UC-22, UC-25..UC-30)."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import ActorDTO, LineType
from backend.features.yarn_costing.dto.dashboard_dto import CheckPriceAnomaliesRequest
from backend.features.yarn_costing.dto.price_dto import (
    CreateAdjustmentLineRequest,
    DeleteAdjustmentLineRequest,
    ExportPriceLinesRequest,
    ListPriceLinesRequest,
    SetAccountingCodeRequest,
)
from backend.features.yarn_costing.dto.pricing_dto import GetYarnDetailRequest, YarnDetailResponse
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest, ReferenceDataResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, download_button, panel, section_title, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.actor_block import render_actor_block
from frontend.features.yarn_costing.components.columns import (
    ANOMALY_CONFIG,
    COMPONENT_CONFIG,
    HISTORY_CONFIG,
    LINE_CONFIG,
    PRICE_LINE_CONFIG,
    STAGE_COST_CONFIG,
    YARN_SUMMARY_CONFIG,
    component_rows,
    history_rows,
    line_rows,
    price_anomaly_rows,
    price_line_rows,
    stage_cost_rows,
    yarn_summary_rows,
)
from frontend.features.yarn_costing.components.dialogs import confirm_dialog
from frontend.features.yarn_costing.components.display import (
    components_text,
    count_text,
    fmt_date,
    from_percent,
    text_or_dash,
    yes_no,
)
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.group_menu import render_group_menu
from frontend.features.yarn_costing.components.labels import (
    ADJUSTMENT_TYPES,
    ALL,
    LINE_TYPE_LABELS,
    STATUS_LABELS,
    STATUS_ORDER,
    TECHNOLOGY_LABELS,
    all_or,
    factory_codes,
    factory_label,
    label_of,
)
from frontend.features.yarn_costing.components.permissions import action_state, explain
from frontend.features.yarn_costing.pages.nsm_pricing_page import OPEN_YARN_KEY, NsmPricingPage

ACCOUNTING_FILTER = {"Có": True, "Chưa có": False}


class PriceListPage(BasePage):
    title = "[Chung] Bảng giá đã tính"
    icon = "💰"
    description = "Xem, lọc, xuất bảng giá sợi; nhập mã kế toán, tạo / xoá dòng chiết khấu - phụ phí và xem chi tiết, lịch sử giá."

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        render_group_menu(self, reference)
        actor = render_actor_block(feature, self.state, reference)
        show_flash(self.state)

        request = self._filters(reference)
        data = feature.list_price_lines(request)
        rate_text = (
            f"Tỷ giá đang dùng: {format_number(data.exchange_rate)} VND/USD (từ {fmt_date(data.exchange_rate_date)})"
            if data.exchange_rate is not None
            else "Chưa có tỷ giá."
        )
        st.info(f"{rate_text} · Hệ số thí nghiệm: {format_number(data.trial_factor, 2)}", icon="💱")
        stat_row(
            [
                ("Tổng dòng", format_number(data.total_count)),
                ("Có mã kế toán", format_number(data.with_accounting_code_count)),
                ("Chưa tính được", format_number(data.not_priced_count)),
                ("Chờ xưởng xem", format_number(data.waiting_count)),
            ]
        )

        with panel("Bảng giá", icon="📋"):
            picked = data_table(
                price_line_rows(data.items),
                column_config=PRICE_LINE_CONFIG,
                selection="single",
                key=self.key("lines"),
                empty_message="Chưa có giá nào phù hợp bộ lọc.",
            )
            self._table_actions(feature, request)

        if picked:
            self._selected_line(feature, actor, str(picked[0]["Mã dòng"]))

    # ---- filters ----
    def _filters(self, reference: ReferenceDataResponse) -> ListPriceLinesRequest:
        factories = reference.factories
        with panel("Bộ lọc", icon="🔎"):
            c1, c2, c3, c4 = st.columns(4)
            factory = c1.selectbox(
                "Xưởng",
                [ALL, *factory_codes(factories)],
                format_func=lambda c: factory_label(factories, c),
                key=self.key("f_factory"),
            )
            line_types = c2.multiselect(
                "Loại dòng",
                list(LINE_TYPE_LABELS),
                default=list(LINE_TYPE_LABELS),
                format_func=lambda v: label_of(LINE_TYPE_LABELS, v),
                placeholder="Tất cả",
                key=self.key("f_line_types"),
            )
            statuses = c3.multiselect(
                "Trạng thái",
                STATUS_ORDER,
                default=[],
                format_func=lambda v: label_of(STATUS_LABELS, v),
                placeholder="Tất cả",
                key=self.key("f_statuses"),
            )
            technology = c4.segmented_control(
                "Công nghệ",
                [ALL, *list(TECHNOLOGY_LABELS)],
                default=ALL,
                format_func=lambda v: v if v == ALL else label_of(TECHNOLOGY_LABELS, v),
                key=self.key("f_tech"),
            )
            d1, d2, d3, d4 = st.columns(4)
            yarn_group = d1.selectbox("Nhóm sợi", [ALL, *reference.yarn_groups], key=self.key("f_group"))
            accounting = d2.segmented_control("Mã kế toán", [ALL, "Có", "Chưa có"], default=ALL, key=self.key("f_acc"))
            priced_from = d3.date_input("Ngày tính giá từ", value=None, format="DD/MM/YYYY", key=self.key("f_from"))
            priced_to = d4.date_input("Ngày tính giá đến", value=None, format="DD/MM/YYYY", key=self.key("f_to"))
            keyword = st.text_input(
                "Từ khoá", placeholder="Mã dòng, tên sợi, mã kế toán", max_chars=200, key=self.key("f_keyword")
            )
        return ListPriceLinesRequest(
            factory_code=all_or(factory),
            line_types=line_types or None,
            statuses=statuses or None,
            technology=all_or(technology),
            yarn_group=all_or(yarn_group),
            has_accounting_code=ACCOUNTING_FILTER.get(accounting or ALL),
            priced_from=priced_from,
            priced_to=priced_to,
            keyword=keyword,
        )

    # ---- buttons under the table ----
    def _table_actions(self, feature: YarnCostingController, request: ListPriceLinesRequest) -> None:
        left, middle, _ = st.columns([1, 1, 3])
        if left.button("Xuất Excel", icon="📤", key=self.key("export")):
            self.state.set("price_export", feature.export_price_lines(ExportPriceLinesRequest(**request.model_dump())))
        if middle.button("Kiểm tra giá bất thường", icon="⚠️", key=self.key("anomaly")):
            self.state.set(
                "price_anomaly",
                feature.check_price_anomalies(CheckPriceAnomaliesRequest(factory_code=request.factory_code)),
            )
        export = self.state.get("price_export")
        if export is not None:
            download_button(export, label="Tải file Excel", key=self.key("export_dl"), primary=True)
        anomaly = self.state.get("price_anomaly")
        if anomaly is not None:
            section_title("Giá bất thường", "⚠️")
            stat_row(
                [
                    ("Nhóm vi phạm", format_number(anomaly.group_count)),
                    ("Cặp vi phạm", format_number(anomaly.pair_count)),
                ]
            )
            data_table(
                price_anomaly_rows(anomaly.items),
                column_config=ANOMALY_CONFIG,
                empty_message="Không có cặp mã nào vi phạm.",
                key=self.key("anomaly_table"),
            )
            if st.button("Ẩn kết quả", type="tertiary", key=self.key("anomaly_hide")):
                self.state.pop("price_anomaly")
                st.rerun()

    # ---- selected line ----
    def _selected_line(self, feature: YarnCostingController, actor: ActorDTO | None, line_code: str) -> None:
        detail = feature.get_yarn_detail(GetYarnDetailRequest(yarn_code=None, line_code=line_code))
        line = next((item for item in detail.lines if item.line_code == line_code), None)
        with panel(f"Dòng đang chọn: {line_code}", icon="🧾"):
            info_tab, stage_tab, lines_tab, history_tab = st.tabs(
                ["Thông tin mã", "Chi tiết công đoạn", "Dòng giá & bản ĐCNSM", "Lịch sử giá"]
            )
            with info_tab:
                self._yarn_info(detail)
            with stage_tab:
                data_table(
                    stage_cost_rows(detail.stage_details),
                    column_config=STAGE_COST_CONFIG,
                    empty_message="Mã này chưa có chi tiết tính giá.",
                    key=self.key("d_stages"),
                )
            with lines_tab:
                data_table(
                    line_rows(detail.lines),
                    column_config=LINE_CONFIG,
                    empty_message="Mã này chưa có dòng giá.",
                    key=self.key("d_lines"),
                )
                section_title("Các bản ĐCNSM cùng mã gốc")
                data_table(
                    yarn_summary_rows(detail.revisions),
                    column_config=YARN_SUMMARY_CONFIG,
                    empty_message="Chưa có bản ĐCNSM.",
                    key=self.key("d_revisions"),
                )
            with history_tab:
                data_table(
                    history_rows(detail.history),
                    column_config=HISTORY_CONFIG,
                    empty_message="Chưa có lịch sử giá.",
                    key=self.key("d_history"),
                )
            self._line_actions(feature, actor, detail, line_code, line)

    def _yarn_info(self, detail: YarnDetailResponse) -> None:
        y = detail.yarn
        facts = [
            ("Mã", y.yarn_code),
            ("Tên sợi", y.yarn_name),
            ("Nhóm sợi", text_or_dash(y.yarn_group)),
            ("Chi số", count_text(y.count)),
            ("Công nghệ", label_of(TECHNOLOGY_LABELS, y.technology)),
            ("Compact", yes_no(y.is_compact)),
            ("Nhóm tiêu hao", text_or_dash(y.loss_group_key)),
            ("Đóng gói", text_or_dash(f"{y.packaging_code} - {y.packaging_name}" if y.packaging_code else "")),
            ("Thành phần", components_text(y.components)),
            ("Trạng thái", label_of(STATUS_LABELS, y.status)),
            ("Khoá", yes_no(y.is_locked)),
            ("Sợi so sánh", text_or_dash(y.reference_yarn_code)),
            ("Lý do khác sợi cùng nhóm", text_or_dash(y.nsm_warning_reason)),
            ("Lý do ĐCNSM", text_or_dash(y.adjust_reason)),
            ("Ngày tính giá", fmt_date(y.first_priced_at)),
            ("Ngày hiệu lực", fmt_date(y.effective_date)),
        ]
        columns = st.columns(3)
        for index, (label, value) in enumerate(facts):
            columns[index % 3].markdown(f"**{label}:** {value}")
        if y.status_reasons:
            st.warning("\n".join(f"- {reason}" for reason in y.status_reasons), icon="⚠️")
        if y.components:
            st.markdown("**Thành phần nguyên liệu**")
            data_table(
                component_rows(y.components),
                column_config=COMPONENT_CONFIG,
                key=self.key("d_components"),
            )
        data_table(
            [{"Công đoạn": s.stage_code, "Tên công đoạn": s.stage_name, "NSM (kg/giờ)": s.nsm} for s in detail.stages],
            column_config={"NSM (kg/giờ)": st.column_config.NumberColumn("NSM (kg/giờ)", format="localized")},
            empty_message="Mã này chưa có NSM.",
            key=self.key("d_nsm"),
        )

    def _line_actions(
        self,
        feature: YarnCostingController,
        actor: ActorDTO | None,
        detail: YarnDetailResponse,
        line_code: str,
        line: object,
    ) -> None:
        yarn = detail.yarn
        factory = str(yarn.factory_code)
        current_code = getattr(line, "accounting_code", None) or ""
        line_type = getattr(line, "line_type", None)
        reasons: list[str | None] = []

        acc_col, button_col = st.columns([3, 1], vertical_alignment="bottom")
        accounting_code = acc_col.text_input(
            "Mã kế toán", value=current_code, max_chars=100, key=self.key(f"acc.{line_code}")
        )
        acc_disabled, acc_why = action_state(self.state, "UC-28", factory)
        reasons.append(acc_why)
        if button_col.button(
            "Lưu mã kế toán", type="primary", key=self.key("acc_save"), disabled=acc_disabled, help=acc_why
        ):
            result = feature.set_accounting_code(
                SetAccountingCodeRequest(actor=actor, line_code=line_code, accounting_code=accounting_code)
            )
            set_flash(self.state, result.message)
            st.rerun()
        st.caption("Để trống rồi bấm Lưu = xoá mã kế toán.")

        adj_disabled, adj_why = action_state(self.state, "UC-25", factory)
        reasons.append(adj_why)
        with st.expander("Thêm CK/PP", icon="➕"), st.form(self.key(f"adj_form.{yarn.yarn_code}")):
            adj_type = st.radio(
                "Loại",
                list(ADJUSTMENT_TYPES),
                format_func=lambda v: label_of(LINE_TYPE_LABELS, v),
                horizontal=True,
                key=self.key(f"adj_type.{yarn.yarn_code}"),
            )
            adj_percent = st.number_input(
                "% chiết khấu / phụ phí",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.5,
                format="%.2f",
                help="Ví dụ 5 = 5%",
                key=self.key(f"adj_percent.{yarn.yarn_code}"),
            )
            adj_reason = st.text_area("Lý do", max_chars=500, key=self.key(f"adj_reason.{yarn.yarn_code}"))
            adj_order = st.text_input(
                "Đơn hàng",
                max_chars=100,
                placeholder="Ví dụ: PO-2026-118",
                key=self.key(f"adj_order.{yarn.yarn_code}"),
            )
            if st.form_submit_button("Lưu dòng CK/PP", type="primary", disabled=adj_disabled, help=adj_why):
                result = feature.create_adjustment_line(
                    CreateAdjustmentLineRequest(
                        actor=actor,
                        yarn_code=yarn.yarn_code,
                        line_type=adj_type or LineType.CHIET_KHAU,
                        percent=from_percent(adj_percent),
                        reason=adj_reason,
                        order_ref=adj_order,
                    )
                )
                set_flash(self.state, result.message)
                st.rerun()

        left, right, _ = st.columns([1, 1, 2])
        if line_type in ADJUSTMENT_TYPES:
            del_disabled, del_why = action_state(self.state, "UC-26", factory)
            if current_code:
                del_disabled, del_why = True, f"Dòng {line_code} đã có mã kế toán, không xoá được."
            reasons.append(del_why)
            if left.button("Xoá dòng CK/PP", icon="🗑️", key=self.key("adj_delete"), disabled=del_disabled, help=del_why):
                confirm_dialog(
                    self.state,
                    self.key(f"dlg.delete_adj.{line_code}"),
                    "Xác nhận xoá dòng CK/PP",
                    f"Xoá dòng {line_code}? Lịch sử giá của dòng vẫn được giữ; số thứ tự CK/PP không dùng lại.",
                    "Xoá dòng",
                    lambda: (
                        feature.delete_adjustment_line(
                            DeleteAdjustmentLineRequest(actor=actor, line_code=line_code)
                        ).message
                    ),
                )
        if right.button("Mở trong Nhập NSM", icon="🧮", key=self.key("open_nsm")):
            self.state.set(OPEN_YARN_KEY, {"yarn_code": yarn.yarn_code, "factory_code": factory})
            self.go_to(NsmPricingPage)
        explain(*reasons)

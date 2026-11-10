"""Screen 9 (`so-sanh-2-soi`) - So sánh 2 sợi (UC-52, bổ sung 2026-11-10)."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.price_dto import ListPriceLinesRequest
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from backend.features.yarn_costing.dto.sales_dto import ComparePriceLinesRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, empty_state, panel
from frontend.features.yarn_costing.components.columns import money, percent
from frontend.features.yarn_costing.components.data_warnings import show_data_warnings
from frontend.features.yarn_costing.components.display import pct, percent_value, plain, usd, vnd

USD_LABEL = "USD/kg"


class ComparePage(BasePage):
    title = "So sánh 2 sợi"
    menu_group = "Dùng chung"
    icon = "⚖️"
    slug = "so-sanh-2-soi"
    description = (
        "Chọn hai dòng giá bất kỳ (cả hai xưởng, cả dòng chiết khấu / phụ phí) để so thông tin, giá và từng công đoạn."
    )

    def render(self) -> None:
        feature = gateway.open(YarnCostingController)
        reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))
        show_data_warnings(reference)
        rows = feature.list_price_lines(ListPriceLinesRequest()).items
        labels = {
            r.line_code: f"{r.line_code} - {r.yarn_name} ({r.factory_code})"
            + (f" · {r.customer_names_text}" if r.customer_names_text else "")
            + (f" · KT {r.accounting_code}" if r.accounting_code else "")
            for r in rows
        }
        codes = list(labels)
        c1, c2 = st.columns(2)
        line_a = c1.selectbox(
            "Sợi A",
            codes,
            index=None,
            placeholder="Gõ mã, tên sợi, tên theo khách hoặc mã kế toán",
            format_func=lambda c: labels.get(c, c),
            key=self.key("line_a"),
        )
        line_b = c2.selectbox(
            "Sợi B",
            codes,
            index=None,
            placeholder="Gõ mã, tên sợi, tên theo khách hoặc mã kế toán",
            format_func=lambda c: labels.get(c, c),
            key=self.key("line_b"),
        )
        if not line_a or not line_b:
            empty_state("Chọn hai dòng giá để so sánh.")
            return
        if line_a == line_b:
            st.warning("Hãy chọn hai dòng giá khác nhau.", icon="⚠️")
            return
        data = feature.compare_price_lines(ComparePriceLinesRequest(line_a=line_a, line_b=line_b))
        with panel("Thông tin", icon="🧵"):
            data_table(
                [{"Mục": r.label, "Sợi A": r.a, "Sợi B": r.b} for r in data.info],
                key=self.key("info"),
            )
        with panel("Giá (VND/kg)", icon="💰"):
            data_table(
                [
                    {
                        "Khoản": r.label,
                        "Sợi A": usd(r.a) if r.label == USD_LABEL else vnd(r.a),
                        "Sợi B": usd(r.b) if r.label == USD_LABEL else vnd(r.b),
                        "Chênh lệch (B − A)": usd(r.difference) if r.label == USD_LABEL else vnd(r.difference),
                        "Chênh lệch %": percent_value(r.difference_percent),
                    }
                    for r in data.prices
                ],
                column_config={
                    "Sợi A": st.column_config.NumberColumn("Sợi A", format="localized"),
                    "Sợi B": st.column_config.NumberColumn("Sợi B", format="localized"),
                    "Chênh lệch (B − A)": st.column_config.NumberColumn("Chênh lệch (B − A)", format="localized"),
                    "Chênh lệch %": percent("Chênh lệch %"),
                },
                key=self.key("prices"),
            )
        with panel("Theo công đoạn", icon="🏭"):
            data_table(
                [
                    {
                        "Công đoạn": r.stage_code,
                        "Tên công đoạn": r.stage_name,
                        "NSM A": plain(r.nsm_a),
                        "NSM B": plain(r.nsm_b),
                        "Tiêu hao A": pct(r.loss_a),
                        "Tiêu hao B": pct(r.loss_b),
                        "Chi phí/kg A": vnd(r.cost_a),
                        "Chi phí/kg B": vnd(r.cost_b),
                    }
                    for r in data.stages
                ],
                column_config={
                    "NSM A": st.column_config.NumberColumn("NSM A", format="localized"),
                    "NSM B": st.column_config.NumberColumn("NSM B", format="localized"),
                    "Tiêu hao A": percent("Tiêu hao A"),
                    "Tiêu hao B": percent("Tiêu hao B"),
                    "Chi phí/kg A": money("Chi phí/kg A"),
                    "Chi phí/kg B": money("Chi phí/kg B"),
                },
                empty_message="Hai dòng giá chưa có chi tiết công đoạn.",
                key=self.key("stages"),
            )

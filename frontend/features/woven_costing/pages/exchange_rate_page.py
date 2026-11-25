"""Screen 6 - Tỷ giá VND/USD theo tháng (UC-05, UC-31)."""

from datetime import date

import streamlit as st

from backend.core.base import EmptyRequest
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import RoleCode
from backend.features.woven_costing.dto.master_dto import SaveExchangeRateRequest
from frontend.core.base_page import BasePage
from frontend.core.components import data_table, panel
from frontend.features.woven_costing.components.errors import attempt
from frontend.features.woven_costing.components.flash import set_flash, show_flash
from frontend.features.woven_costing.components.labels import dec, num
from frontend.features.woven_costing.components.roles import has_any


class ExchangeRatePage(BasePage):
    title = "Tỷ giá"
    icon = "💱"
    slug = "ty-gia"
    menu_group = "Phòng SO"
    description = "Tỷ giá VND/USD theo tháng dùng cho costsheet."

    def render(self) -> None:
        show_flash(self.state)
        feature = gateway.open(WovenCostingController)
        today = date.today()
        if has_any(RoleCode.SO.value):
            with st.form(self.key("form")):
                c1, c2, c3 = st.columns(3)
                month = c1.selectbox(
                    "Tháng", list(range(1, 13)), index=today.month - 1, format_func=lambda m: f"{m:02d}",
                    key=self.key("month"),
                )  # fmt: skip
                year = c2.number_input(
                    "Năm", min_value=2020, max_value=2100, value=today.year, step=1, key=self.key("year")
                )
                rate = c3.number_input(
                    "Tỷ giá (VND/USD)", min_value=0.0, value=None, step=10.0, format="%.2f", key=self.key("rate")
                )
                submitted = st.form_submit_button("Lưu tỷ giá", type="primary", icon=":material/save:")
            if submitted:
                saved = attempt(
                    lambda: feature.save_exchange_rate(
                        SaveExchangeRateRequest(month=int(month), year=int(year), rate=dec(rate) or dec(0))
                    )
                )
                if saved is not None:
                    set_flash(self.state, saved.message)
                    st.rerun()
        with panel("Các tháng đã nhập", icon="📅"):
            data_table(
                [
                    {
                        "Tháng": r.month,
                        "Năm": r.year,
                        "Tỷ giá": num(r.rate),
                        "Người cập nhật": r.updated_by,
                        "Lúc cập nhật": r.updated_at,
                    }
                    for r in feature.list_exchange_rates(EmptyRequest()).rows
                ],
                column_config={
                    "Tháng": st.column_config.NumberColumn("Tháng", format="%02d", width="small"),
                    "Năm": st.column_config.NumberColumn("Năm", format="%d", width="small"),
                    "Tỷ giá": st.column_config.NumberColumn("Tỷ giá", format="localized"),
                    "Lúc cập nhật": st.column_config.DatetimeColumn("Lúc cập nhật", format="DD/MM/YYYY HH:mm"),
                },
                empty_message="Chưa có tỷ giá nào.",
            )

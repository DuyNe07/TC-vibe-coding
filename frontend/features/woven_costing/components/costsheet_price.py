"""Screen 2 tab "Giá bán & lợi nhuận" (block F)."""

from typing import Any

import streamlit as st

from backend.features.woven_costing.dto.common_dto import Currency, PriceType, SaleForm
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse
from frontend.core.base_page import BasePage
from frontend.core.components import data_table
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.labels import (
    RED_FLAG,
    dec,
    enum_values,
    num,
    pct_text,
    text,
    text_or_empty,
)
from frontend.features.woven_costing.components.marks import apply_table, heading

FREIGHT_LABELS = {
    PriceType.CIF.value: "F&I (đ/m)",
    PriceType.CIP.value: "F&I (đ/m)",
    PriceType.CPT.value: "Phí vận chuyển (đ/m)",
}
COGS_COLUMNS = ["Tên", "Đơn giá (đ/m)", "Ghi chú"]


def _profit_table(w: CostsheetResponse) -> None:
    rows = []
    for row in w.result.profit_rows:
        if row.is_percent:
            vnd, usd = pct_text(row.vnd), ""
        else:
            vnd = format_number(row.vnd) if row.vnd is not None else ""
            usd = format_number(row.usd, 4) if row.usd is not None else ""
        rows.append({"Khoản": row.label, "VND/m": vnd, "USD/m": usd, "⚑": RED_FLAG if row.below_threshold else ""})
    data_table(
        rows,
        column_config={"⚑": st.column_config.TextColumn("⚑", width="small")},
        empty_message="Chưa tính được lợi nhuận (cần giá bán).",
    )


def price_tab(page: BasePage, w: CostsheetResponse, sfx: str, price_type: str | None) -> dict[str, Any] | None:
    """Returns the PriceInputDTO fields (None = read only)."""
    price = w.input.price
    off = not w.editable

    def key(name: str) -> str:
        return page.key(f"price.{name}.{sfx}")

    heading("Giá bán", editable=not off)  # UI change 2026-11-27
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        currency = st.segmented_control(
            "Đơn vị giá bán",
            enum_values(Currency),
            default=text(price.sell_price_currency) or Currency.USD.value,
            required=True,
            key=key("currency"),
            disabled=off,
        )
    job = text(w.input.sale_form) in (SaleForm.WEAVING_JOB.value, SaleForm.DYEING_JOB.value)  # BR-89, BR-90
    sell_label = "Giá bán (phí gia công) chưa VAT (/m)" if job else "Giá bán chưa VAT (/m)"
    sell = c2.number_input(sell_label, min_value=0.0, value=num(price.sell_price_input), format="%.4f",
                           key=key("sell"), disabled=off)  # fmt: skip
    commission = c3.number_input(
        "Commission (đ/m)", min_value=0.0, value=num(price.commission), key=key("commission"), disabled=off
    )
    interest = c4.number_input(
        "Lãi vay (đ/m)", min_value=0.0, value=num(price.interest_cost), key=key("interest"), disabled=off
    )
    c1, c2, _, _ = st.columns(4)
    freight = dec(0)
    freight_label = FREIGHT_LABELS.get(price_type or "")
    if freight_label:
        freight = dec(
            c1.number_input(
                freight_label, min_value=0.0, value=num(price.freight_insurance), key=key("freight"), disabled=off
            )
        )
    ship_date = c2.date_input("Ngày shipment", value=price.ship_date, format="DD/MM/YYYY", key=key("ship"),
                              disabled=off)  # fmt: skip
    heading("Chi phí vào giá vốn (tối đa 10)", editable=not off)
    rows = [{"Tên": c.name, "Đơn giá (đ/m)": num(c.amount), "Ghi chú": c.note} for c in price.cogs_extra_lines]
    config = {"Đơn giá (đ/m)": st.column_config.NumberColumn("Đơn giá (đ/m)", min_value=0, format="localized")}
    cogs = None
    if off:
        data_table(rows, column_config=config, empty_message="Không có chi phí vào giá vốn.")
    else:
        edited = apply_table(rows, key=key("cogs"), columns=COGS_COLUMNS, column_config=config, allow_add_delete=True)
        cogs = [
            {
                "name": text_or_empty(r.get("Tên")),
                "amount": dec(r.get("Đơn giá (đ/m)")),
                "note": text_or_empty(r.get("Ghi chú")),
            }
            for r in edited
            if text_or_empty(r.get("Tên")) or r.get("Đơn giá (đ/m)") is not None
        ]
    heading("Lợi nhuận", editable=False)
    _profit_table(w)
    r = w.result
    st.caption(f"Ngưỡng cảnh báo: GP% {pct_text(r.gp_threshold)}, OP% {pct_text(r.op_threshold)} (SO đặt).")
    if off:
        return None
    return {
        "sell_price_currency": currency or Currency.USD.value,
        "sell_price_input": dec(sell),
        "cogs_extra_lines": cogs or [],
        "commission": dec(commission),
        "freight_insurance": freight,
        "interest_cost": dec(interest),
        "ship_date": ship_date,
    }

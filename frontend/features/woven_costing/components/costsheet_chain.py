"""Screen 2 (UI change 2026-11-23, a tab since 2026-11-27): "Chuỗi nhu cầu" and the warnings shown at the top of each
tab."""

import streamlit as st

from backend.features.woven_costing.dto.common_dto import WarningDTO
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse
from frontend.core.components import data_table, empty_state
from frontend.core.formatting import format_number
from frontend.features.woven_costing.components.labels import num, text
from frontend.features.woven_costing.components.marks import heading

CHAIN_CONFIG = {
    "Bước": st.column_config.TextColumn("Bước", width="medium", pinned=True),
    "Số lượng (m)": st.column_config.TextColumn("Số lượng (m)"),
    "Số lượng (kg)": st.column_config.TextColumn("Số lượng (kg)"),
    "Hao hụt áp dụng": st.column_config.TextColumn("Hao hụt áp dụng", width="large"),
    "Chi phí (đ)": st.column_config.TextColumn("Chi phí (đ)"),
    "Chi phí/m TP (đ/m)": st.column_config.TextColumn("Chi phí/m TP (đ/m)"),
}


def _round(value: object, digits: int) -> str:
    """Vietnamese-formatted number; an empty cell stays blank (a number column would show "None")."""
    number = num(value)
    return "" if number is None else format_number(number, digits)


def demand_chain_tab(w: CostsheetResponse) -> None:
    """Read-only table worked back from the finished meters sold to the yarn (tab "Chuỗi nhu cầu" since 2026-11-27,
    before: a block between "Thông tin đơn" and the tabs)."""
    heading("Chuỗi nhu cầu", editable=False, icon="🔗")
    st.caption("Tính ngược từ thành phẩm giao khách đến sợi.")
    if not w.result.calculated or not w.result.demand_chain:
        empty_state("Chưa có chuỗi nhu cầu.", "Điền Thông tin đơn để app tính số lượng và chi phí từng bước.")
        return
    data_table(
        [
            {
                "Bước": s.step,
                "Số lượng (m)": _round(s.meters, 1),
                "Số lượng (kg)": _round(s.kg, 1),
                "Hao hụt áp dụng": s.losses,
                "Chi phí (đ)": _round(s.cost, 0),
                "Chi phí/m TP (đ/m)": _round(s.cost_per_m, 2),
            }
            for s in w.result.demand_chain
        ],
        column_config=CHAIN_CONFIG,
    )


def section_warnings(warnings: list[WarningDTO], section: str) -> list[WarningDTO]:
    return [w for w in warnings if text(w.section) == section]


def show_warnings(warnings: list[WarningDTO]) -> None:
    """Warnings of one tab, at its top: blocking ones as errors."""
    for warning in warnings:
        if warning.blocking:
            st.error(warning.message, icon="⛔")
        else:
            st.warning(warning.message, icon="⚠️")

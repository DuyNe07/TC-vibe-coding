"""Khối chênh lệch của một lần tính lại (UC-37): Screen 5, nút "Xem chênh lệch", Screen 7."""

from typing import Any

import streamlit as st

from backend.features.yarn_costing.dto.master_dto import GetRecalcDiffRequest
from frontend.core.components import data_table, download_button, stat_row
from frontend.core.formatting import format_number
from frontend.features.yarn_costing.components.columns import money, percent
from frontend.features.yarn_costing.components.display import percent_text, percent_value, vnd
from frontend.features.yarn_costing.components.labels import LINE_TYPE_LABELS, label_of

DIFF_CONFIG = {
    "Tổng trước": money("Tổng trước"),
    "Tổng sau": money("Tổng sau"),
    "Chênh lệch (VND)": money("Chênh lệch (VND)"),
    "Chênh lệch (%)": percent("Chênh lệch (%)"),
}


def render_recalc_diff(feature: Any, batch_id: str, key: str) -> None:
    """Ô số liệu + bảng chênh lệch + "Xuất Excel" của một lần tính lại."""
    types = st.multiselect(
        "Loại dòng",
        list(LINE_TYPE_LABELS),
        default=[],
        format_func=lambda v: label_of(LINE_TYPE_LABELS, v),
        placeholder="Tất cả",
        key=f"{key}.types",
    )
    diff = feature.get_recalc_diff(GetRecalcDiffRequest(batch_id=batch_id, line_types=types or None))
    stat_row(
        [
            ("Dòng tăng", format_number(diff.up_count)),
            ("Dòng giảm", format_number(diff.down_count)),
            ("Không đổi", format_number(diff.unchanged_count)),
            ("Chênh lệch % trung bình", percent_text(diff.avg_percent)),
        ]
    )
    data_table(
        [
            {
                "Mã dòng": row.line_code,
                "Tên sợi": row.yarn_name,
                "Loại dòng": row.line_type.value,
                "Tổng trước": vnd(row.old_total),
                "Tổng sau": vnd(row.new_total),
                "Chênh lệch (VND)": vnd(row.diff_vnd),
                "Chênh lệch (%)": percent_value(row.diff_percent),
            }
            for row in diff.items
        ],
        column_config=DIFF_CONFIG,
        empty_message="Không có dòng giá nào thay đổi.",
        key=f"{key}.table",
    )
    download_button(diff.file, label="Xuất Excel", key=f"{key}.export")


def open_recalc_diff_dialog(feature: Any, batch_id: str, key: str) -> None:
    @st.dialog(f"Chênh lệch lần tính lại {batch_id}", width="large")
    def _dialog() -> None:
        render_recalc_diff(feature, batch_id, key)

    _dialog()

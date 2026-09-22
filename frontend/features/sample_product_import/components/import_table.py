"""Table of import rows with their action and errors."""

import streamlit as st

from backend.features.sample_product_import.dto.import_dto import ImportRowResultDTO
from frontend.core.components import data_table
from frontend.features.sample_product_import.components.labels import ACTION_LABELS


def import_rows_table(rows: list[ImportRowResultDTO], key: str) -> None:
    data_table(
        [
            {
                "Dòng": r.row_number,
                "Kết quả": ACTION_LABELS[r.action],
                "Mã SP": r.code,
                "Tên sản phẩm": r.name,
                "Số lượng": r.quantity,
                "Đơn giá": r.unit_price,
                "Lỗi": " | ".join(r.errors),
            }
            for r in rows
        ],
        column_config={"Đơn giá": st.column_config.NumberColumn(format="localized")},
        key=key,
    )

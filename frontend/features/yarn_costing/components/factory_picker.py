"""Chọn xưởng dạng nút (S1 | S4) dùng ở Screen 3-6."""

import streamlit as st

from backend.features.yarn_costing.dto.reference_dto import FactoryDTO
from frontend.features.yarn_costing.components.labels import factory_codes, factory_label


def factory_segment(factories: list[FactoryDTO], key: str, preferred: str | None = None) -> str | None:
    """Nút chọn xưởng bắt buộc; mặc định xưởng của nhóm đang thao tác (nếu có) hoặc xưởng đầu tiên."""
    codes = factory_codes(factories)
    if not codes:
        return None
    if st.session_state.get(key) not in codes:
        st.session_state.pop(key, None)
    default = None if key in st.session_state else (preferred if preferred in codes else codes[0])
    value = st.segmented_control(
        "Xưởng",
        codes,
        default=default,
        required=True,
        format_func=lambda c: factory_label(factories, c),
        key=key,
    )
    return value or codes[0]

"""Tắt nút theo quyền (BR-46, BR-47, BR-48) - chỉ để hiển thị; backend vẫn là nơi quyết định."""

import streamlit as st

from frontend.core.session_state import SessionState
from frontend.features.yarn_costing.components.actor_block import current_actor

_FACTORY_UCS = {
    "UC-11", "UC-12", "UC-13", "UC-14", "UC-18", "UC-20", "UC-21", "UC-23", "UC-24", "UC-25", "UC-26", "UC-28", "UC-34",
    "UC-45",
}  # fmt: skip
UC_BY_GROUP: dict[str, set[str] | None] = {
    "SALES": {"UC-15", "UC-16", "UC-17"},
    "XS1": _FACTORY_UCS,
    "XS4": _FACTORY_UCS,
    "KT": {"UC-28"},
    "SO": None,  # Phòng SO: mọi thao tác
}
NOT_AUTHENTICATED = "Vui lòng chọn nhóm, nhập đúng mã nội bộ và chọn tên của bạn."


def action_state(state: SessionState, uc: str, factory_code: str | None = None) -> tuple[bool, str | None]:
    """(disabled, help) cho một nút thao tác."""
    info = current_actor(state)
    if not info:
        return True, NOT_AUTHENTICATED
    allowed = UC_BY_GROUP.get(str(info["group_code"]), set())
    if allowed is not None and uc not in allowed:
        return True, f"Nhóm '{info['group_name']}' không được thực hiện thao tác này."
    if info.get("factory_code") and factory_code and str(info["factory_code"]) != str(factory_code):
        return True, f"Bạn chỉ được thao tác dữ liệu của xưởng {info['factory_code']}."
    return False, None


def explain(*reasons: str | None) -> None:
    """Chú thích dưới nhóm nút bị tắt (mục 8: nút không có quyền bị tắt kèm chú thích)."""
    shown: list[str] = []
    for reason in reasons:
        if reason and reason not in shown:
            shown.append(reason)
    for reason in shown:
        st.caption(f"🔒 {reason}")

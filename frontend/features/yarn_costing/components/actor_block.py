"""Khối "Người thao tác" (UC-39, BR-46) dùng chung cho Screen 1-6 và 8.

Người thao tác đã xác thực được nhớ trong `SessionState` của chức năng (không qua `self.key()`), nên dùng chung cho mọi
trang trong phiên làm việc; có nút "Đổi người thao tác". Backend vẫn kiểm tra lại BR-46 ở mỗi thao tác.
"""

from typing import Any

import streamlit as st

from backend.core.exceptions import AppError
from backend.features.yarn_costing.dto.common_dto import ActorDTO
from backend.features.yarn_costing.dto.reference_dto import ReferenceDataResponse
from backend.features.yarn_costing.dto.user_dto import VerifyActorRequest
from frontend.core.components import panel, show_error
from frontend.core.session_state import SessionState

ACTOR_KEY = "actor"


def current_actor(state: SessionState) -> dict[str, Any] | None:
    return state.get(ACTOR_KEY)


def clear_actor(state: SessionState) -> None:
    state.pop(ACTOR_KEY)


def actor_dto(state: SessionState) -> ActorDTO | None:
    info = current_actor(state)
    if not info:
        return None
    return ActorDTO(group_code=info["group_code"], access_code=info["access_code"], person_name=info["person_name"])


def actor_factory(state: SessionState) -> str | None:
    """Xưởng của nhóm đang thao tác (nhóm Xưởng S1 / S4), None với các nhóm khác."""
    info = current_actor(state)
    return str(info["factory_code"]) if info and info.get("factory_code") else None


def actor_is_so(state: SessionState) -> bool:
    info = current_actor(state)
    return bool(info) and info["group_code"] == "SO"


def render_actor_block(feature: Any, state: SessionState, reference: ReferenceDataResponse) -> ActorDTO | None:
    """Hiện khối xác thực; trả ActorDTO đã xác thực (UC-39) hoặc None."""
    info = current_actor(state)
    with panel("Người thao tác", icon="🔐"):
        if info:
            left, right = st.columns([4, 1], vertical_alignment="center")
            left.success(f"Đang thao tác: {info['group_name']} - {info['person_name']}.", icon="👤")
            if right.button("Đổi người thao tác", key=state.key("actor.change")):
                clear_actor(state)
                st.rerun()
            return actor_dto(state)
        st.caption(
            "Chọn nhóm, nhập mã nội bộ của nhóm và chọn tên của bạn. Chỉ cần làm một lần trong phiên làm việc; "
            "xem, tra cứu và xuất file không cần xác thực."
        )
        groups = [g for g in reference.groups if g.active]
        by_code = {g.code: g for g in groups}
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1], vertical_alignment="bottom")
        group_code = c1.selectbox(
            "Nhóm",
            list(by_code),
            index=None,
            placeholder="Chọn nhóm",
            format_func=lambda code: by_code[code].name if code in by_code else str(code),
            key=state.key("actor.group"),
        )
        access_code = c2.text_input("Mã nội bộ", type="password", key=state.key("actor.access_code"))
        group = by_code.get(group_code) if group_code else None
        names = list(group.active_member_names) if group else []
        person_name = c3.selectbox(
            "Tên của bạn",
            names,
            index=None,
            placeholder="Chọn tên",
            disabled=not names,
            key=state.key(f"actor.person.{group_code}"),
        )
        ready = bool(group_code and access_code and person_name)
        if c4.button("Xác nhận", type="primary", key=state.key("actor.confirm"), disabled=not ready):
            actor = ActorDTO(group_code=group_code, access_code=access_code, person_name=person_name)
            try:
                result = feature.verify_actor(VerifyActorRequest(actor=actor))
            except AppError as exc:
                show_error(exc)
            else:
                state.set(
                    ACTOR_KEY,
                    {
                        "group_code": result.group_code,
                        "group_name": result.group_name,
                        "person_name": result.person_name,
                        "factory_code": result.factory_code,
                        "access_code": access_code,
                    },
                )
                st.rerun()
        if group is not None and not names:
            st.caption(
                "Nhóm này chưa có thành viên đang hoạt động. Phòng SO khai báo thành viên ở trang 'Người dùng & nhật ký'."
            )
        return None

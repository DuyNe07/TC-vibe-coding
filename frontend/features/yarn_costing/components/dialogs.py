"""Hộp thoại xác nhận trước các thao tác quan trọng (mục 8 "Hộp thoại xác nhận")."""

from collections.abc import Callable

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from backend.core.exceptions import AppError, InvalidInputError
from frontend.core.components import show_error
from frontend.core.session_state import SessionState
from frontend.features.yarn_costing.components.flash import set_flash


def confirm_dialog(
    state: SessionState,
    key: str,
    title: str,
    question: str,
    confirm_label: str,
    action: Callable[[], str],
    on_done: Callable[[], None] | None = None,
) -> None:
    """Mở hộp thoại; bấm xác nhận -> `action()` (gọi controller, trả thông báo) -> thông báo + tải lại trang.

    Lỗi nghiệp vụ hiện ngay trong hộp thoại để người dùng sửa rồi thử lại.
    """

    @st.dialog(title)
    def _dialog() -> None:
        st.write(question)
        yes, no = st.columns(2)
        if yes.button(confirm_label, type="primary", key=f"{key}.yes"):
            try:
                message = action()
            except AppError as exc:
                show_error(exc)
            except PydanticValidationError as exc:
                show_error(InvalidInputError.from_pydantic(exc))
            else:
                set_flash(state, message)
                if on_done is not None:
                    on_done()
                st.rerun()
        if no.button("Không", key=f"{key}.no"):
            st.rerun()

    _dialog()

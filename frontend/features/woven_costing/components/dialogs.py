"""Confirmation dialog before the important actions (section 8: Gửi duyệt, Duyệt, Trả lại, Chốt đơn, Hủy...)."""

from collections.abc import Callable, Sequence

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from backend.core.current_user import get_current_user, set_current_user
from backend.core.exceptions import AppError, InvalidInputError
from frontend.core.session_state import SessionState
from frontend.features.woven_costing.components.errors import show_error_list
from frontend.features.woven_costing.components.flash import set_flash

ActionResult = tuple[str, Sequence[str]]


def confirm_dialog(
    state: SessionState,
    key: str,
    title: str,
    question: str,
    confirm_label: str,
    action: Callable[[str | None], ActionResult],
    reason_label: str | None = None,
    notes: Sequence[str] = (),
    on_done: Callable[[], None] | None = None,
) -> None:
    """Open the dialog; on confirm run ``action(reason)`` -> (message, warnings), flash them and reload the page.

    Business errors stay inside the dialog so the user can fix and retry.
    """
    user = get_current_user()  # the dialog reruns on its own: keep who clicked (permissions, history)

    @st.dialog(title, width="medium")
    def _dialog() -> None:
        set_current_user(user)
        st.write(question)
        for note in notes:
            st.warning(note, icon="⚠️")
        reason = st.text_area(reason_label, max_chars=500, key=f"{key}.reason") if reason_label else None
        with st.container(horizontal=True, gap="small"):
            yes = st.button(confirm_label, type="primary", key=f"{key}.yes")
            no = st.button("Không", key=f"{key}.no")
        if yes:
            try:
                with st.spinner("Đang xử lý, vui lòng chờ…"):
                    message, warnings = action(reason)
            except AppError as exc:
                show_error_list(exc)
            except PydanticValidationError as exc:
                show_error_list(InvalidInputError.from_pydantic(exc))
            else:
                set_flash(state, message, warnings)
                if on_done is not None:
                    on_done()
                st.rerun()
        if no:
            st.rerun()

    _dialog()

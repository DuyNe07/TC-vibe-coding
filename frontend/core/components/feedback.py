"""User feedback: business errors (AppError), unexpected errors, success messages."""

import traceback

import streamlit as st

from backend.core.exceptions import AppError


def show_error(exc: AppError) -> None:
    """Friendly message of an expected error raised by the backend (validation, rule, file...)."""
    st.error(exc.message, icon="⚠️")
    if exc.details:
        with st.expander("Chi tiết lỗi"):
            st.write(exc.details)


def show_unexpected_error(exc: BaseException) -> None:
    st.error("Trang gặp lỗi không mong muốn. Hãy gửi phần chi tiết bên dưới cho người phát triển / AI.", icon="🛑")
    with st.expander("Chi tiết kỹ thuật"):
        st.code("".join(traceback.format_exception(exc)), language="text")


def show_success(message: str) -> None:
    st.success(message, icon="✅")

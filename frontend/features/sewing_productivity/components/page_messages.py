"""Messages of the data screens: no right to open them (BR-09) and the note left by a save before its rerun."""

import streamlit as st

from backend.core.exceptions import AppError
from frontend.core.session_state import SessionState

FLASH = "flash"


def show_no_permission(exc: AppError) -> None:
    """BR-09 as a plain warning: the backend decided, the page only shows the sentence and stops."""
    st.warning(exc.message, icon=":material/lock:")


def leave_flash(state: SessionState, message: str) -> None:
    """Keep the message of a save for the next run: the save is followed by st.rerun(), which would drop a toast."""
    state.set(FLASH, message)


def show_flash(state: SessionState) -> None:
    message = state.pop(FLASH, None)
    if message:
        st.toast(message, icon=":material/check:", duration="long")

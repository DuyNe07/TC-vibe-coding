"""Short success message (and warnings) that survive the rerun done after an action."""

from collections.abc import Sequence

import streamlit as st

from frontend.core.components import show_success
from frontend.core.session_state import SessionState

FLASH_KEY = "flash"
FLASH_WARNINGS_KEY = "flash_warnings"


def set_flash(state: SessionState, message: str, warnings: Sequence[str] = ()) -> None:
    if message:
        current = state.get(FLASH_KEY)
        state.set(FLASH_KEY, f"{current} {message}" if current else message)
    if warnings:
        state.set(FLASH_WARNINGS_KEY, [*state.get(FLASH_WARNINGS_KEY, []), *warnings])


def show_flash(state: SessionState) -> None:
    message = state.pop(FLASH_KEY)
    if message:
        show_success(message)
    for warning in state.pop(FLASH_WARNINGS_KEY, None) or []:
        st.warning(warning, icon="⚠️")

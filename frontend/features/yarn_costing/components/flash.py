"""Success message that survives the rerun done after an action."""

from frontend.core.components import show_success
from frontend.core.session_state import SessionState

FLASH_KEY = "flash"


def set_flash(state: SessionState, message: str) -> None:
    if message:
        current = state.get(FLASH_KEY)
        state.set(FLASH_KEY, f"{current} {message}" if current else message)


def show_flash(state: SessionState) -> None:
    message = state.pop(FLASH_KEY)
    if message:
        show_success(message)

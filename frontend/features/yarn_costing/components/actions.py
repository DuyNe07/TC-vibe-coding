"""Save / preview actions shared by screens (bổ sung 2026-11-11): business errors show in place, success after a rerun."""

from collections.abc import Callable
from typing import Any

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from backend.core.exceptions import AppError, InvalidInputError
from frontend.core.components import show_error
from frontend.core.session_state import SessionState
from frontend.features.yarn_costing.components.flash import set_flash


def run_save(state: SessionState, action: Callable[[], str], on_done: Callable[[], None] | None = None) -> None:
    """Run a save without confirmation: business errors show here, success = message after the rerun."""
    try:
        message = action()
    except AppError as exc:
        show_error(exc)
        return
    except PydanticValidationError as exc:
        show_error(InvalidInputError.from_pydantic(exc))
        return
    set_flash(state, message)
    if on_done is not None:
        on_done()
    st.rerun()


def try_call(action: Callable[[], Any]) -> Any:
    """Run a read / preview: a business error is shown here and the rest of the page keeps rendering (None returned)."""
    try:
        return action()
    except AppError as exc:
        show_error(exc)
    except PydanticValidationError as exc:
        show_error(InvalidInputError.from_pydantic(exc))
    return None

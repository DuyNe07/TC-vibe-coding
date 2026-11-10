"""Helpers shared by the 3 screens of đợt 2 (bổ sung 2026-11-10): access message (BR-84), month pickers, save actions."""

from collections.abc import Callable
from datetime import date
from typing import Any

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from backend.core.exceptions import AppError, InvalidInputError
from frontend.core.components import show_error
from frontend.core.session_state import SessionState
from frontend.features.yarn_costing.components.flash import set_flash
from frontend.features.yarn_costing.components.permissions import action_state

MATERIAL_DENIED = "Chỉ Sales hoặc Phòng SO được xem và thao tác giá nguyên liệu, giá báo khách."
MONTHS_BACK = 12
MONTHS_AHEAD = 3


def material_denied(use_case: str) -> bool:
    """BR-84: accounts without the Sales / Phòng SO role see only the message (the backend refuses them too)."""
    disabled, _ = action_state(use_case)
    if disabled:
        st.warning(MATERIAL_DENIED, icon="🔒")
    return disabled


def month_text(period: str) -> str:
    if not period:
        return ""
    year, month = period.split("-")
    return f"{month}/{year}"


def current_period() -> str:
    today = date.today()
    return f"{today.year:04d}-{today.month:02d}"


def month_options(extra: list[str] | None = None) -> list[str]:
    """Newest first: 3 months ahead … 12 months back, plus any period already used."""
    today = date.today()
    months = set(extra or [])
    for offset in range(-MONTHS_BACK, MONTHS_AHEAD + 1):
        index = today.year * 12 + today.month - 1 + offset
        months.add(f"{index // 12:04d}-{index % 12 + 1:02d}")
    return sorted(months, reverse=True)


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

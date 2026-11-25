"""Errors shown as a list, one sentence per line (section 8: "lỗi hiện thành danh sách, mỗi lỗi 1 dòng")."""

from collections.abc import Callable
from typing import Any, TypeVar

import streamlit as st
from pydantic import ValidationError as PydanticValidationError

from backend.core.exceptions import AppError, InvalidInputError

T = TypeVar("T")


def _items(details: Any) -> list[str]:
    if isinstance(details, (list, tuple)):
        items = []
        for item in details:
            if isinstance(item, dict):
                items.append(str(item.get("message") or item.get("msg") or ""))
            else:
                items.append(str(item))
        return [i for i in items if i]
    if isinstance(details, dict):
        return [str(v) for v in details.values() if v]
    return []


def show_error_list(exc: AppError) -> None:
    items = _items(exc.details)
    if isinstance(exc, InvalidInputError) or len(items) <= 1:
        st.error(exc.message, icon="⚠️")
        return
    header = [line for line in exc.message.splitlines() if line.strip() and line.strip() not in items]
    if not header or "; ".join(items) in header:
        header = ["Chưa thực hiện được, hãy sửa các mục sau:"]
    st.error("\n\n".join(header) + "\n\n" + "\n".join(f"- {item}" for item in items), icon="⚠️")


def attempt(action: Callable[[], T]) -> T | None:
    """Run a controller call; on a business error show it as a list and return None (the page keeps rendering)."""
    try:
        return action()
    except AppError as exc:
        show_error_list(exc)
    except PydanticValidationError as exc:
        show_error_list(InvalidInputError.from_pydantic(exc))
    return None

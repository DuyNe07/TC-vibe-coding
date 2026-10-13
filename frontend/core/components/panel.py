"""Layout building blocks: panel, stat_row, empty_state, section_title.

with panel("Bộ lọc", icon="🔎", description="Lọc theo từ khoá"):
    keyword = st.text_input(...)

stat_row([("Tổng", 120), ("Hợp lệ", 118), ("Lỗi", 2)])
"""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import streamlit as st


@contextmanager
def panel(title: str | None = None, *, icon: str = "", description: str = "", key: str | None = None) -> Iterator[None]:
    """Bordered card grouping related widgets. Use it for every logical block of a page."""
    with st.container(border=True, key=key):
        if title:
            st.markdown(f"**{icon} {title}**" if icon else f"**{title}**")
        if description:
            st.caption(description)
        yield


def stat_row(items: Sequence[tuple[str, Any]] | Sequence[tuple[str, Any, str]]) -> None:
    """A row of KPI tiles: ``[(label, value), ...]`` or ``[(label, value, help), ...]``."""
    if not items:
        return
    for column, item in zip(st.columns(len(items)), items, strict=True):
        label, value, *rest = item
        column.metric(label, value, help=rest[0] if rest else None, border=True)


def empty_state(message: str, hint: str = "", icon: str = "📭") -> None:
    with st.container(border=True):
        st.markdown(f"{icon} **{message}**" + (f"\n\n{hint}" if hint else ""), text_alignment="center")


def section_title(text: str, icon: str = "") -> None:
    st.markdown(f"#### {icon} {text}".strip())

"""Screen 2 (UI change 2026-11-27): input vs read-only marks so sales see at once where to type.

- ``heading``: the title strip of a block / table - blue background + "Nhập liệu" badge when it can be edited, grey
  background + "Chỉ xem" badge otherwise (native Markdown colours only: features never add page CSS).
- ``tab_label``: ✏️ in front of a tab that has cells to type in.
- ``guide``: the 4-step line at the top of an editable costsheet.
- ``apply_table``: an editable table typed in one go, calculated by its "Áp dụng & tính" button.
"""

from typing import Any

import streamlit as st

from frontend.core.components import editable_table

APPLY = "Áp dụng & tính"
INPUT_BADGE = "Nhập liệu"
VIEW_BADGE = "Chỉ xem"
PEN = "✏️"
GUIDE = "① Điền Thông tin đơn → ② Nhập ở các thẻ ✏️ → ③ Xem Giá bán & lợi nhuận → ④ Lưu nháp / Gửi duyệt"


def heading_text(title: str, *, editable: bool, icon: str = "", extra: str = "") -> str:
    """Markdown of the title strip: blue for an input block, grey for a read-only one."""
    color, badge = ("blue", INPUT_BADGE) if editable else ("gray", VIEW_BADGE)
    label = f"{icon} {title}".strip()
    tail = f" {extra}" if extra else ""
    return f"#### :{color}-background[{label}] :{color}-badge[{badge}]{tail}"


def heading(title: str, *, editable: bool, icon: str = "", extra: str = "") -> None:
    st.markdown(heading_text(title, editable=editable, icon=icon, extra=extra))


def tab_label(name: str, *, editable: bool, warnings: int = 0) -> str:
    """Tab title: "✏️ Sợi (2)" when the tab can be edited and has 2 warnings."""
    label = f"{PEN} {name}" if editable else name
    return f"{label} ({warnings})" if warnings else label


def apply_table(rows: list[dict[str, Any]], *, key: str, **kwargs: Any) -> list[dict[str, Any]]:
    """Editable table typed in one go (2026-11-27): the table runs on its own, so a typed cell does not recalculate the
    costsheet; "Áp dụng & tính" under it draws the whole page again, which calculates (UC-16). Lưu nháp / Gửi duyệt
    also draw the whole page, so the typed cells are always taken."""

    @st.fragment
    def table() -> list[dict[str, Any]]:
        edited = editable_table(rows, key=key, **kwargs)
        if st.button(APPLY, key=f"{key}.apply", icon=":material/calculate:"):
            st.rerun(scope="app")
        return edited

    return table()


def guide(editable: bool) -> None:
    """The 4-step guide, only on a costsheet that can still be edited."""
    if editable:
        st.info(GUIDE, icon=":material/route:")

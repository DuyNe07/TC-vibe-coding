"""Display helpers: status badges, rate <-> percent (display unit only), Vietnamese numbers."""

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from typing import Any

import streamlit as st

from backend.features.woven_costing.dto.common_dto import CostsheetStatus
from frontend.core.formatting import format_number

HUNDRED = Decimal(100)
STATUS_STYLE: dict[str, tuple[str, str]] = {
    CostsheetStatus.NHAP.value: ("gray", ":material/edit_note:"),
    CostsheetStatus.CHO_DUYET.value: ("orange", ":material/hourglass_top:"),
    CostsheetStatus.TRA_LAI.value: ("red", ":material/undo:"),
    CostsheetStatus.DA_DUYET.value: ("green", ":material/check:"),
    CostsheetStatus.DA_CHOT_DON.value: ("blue", ":material/verified:"),
    CostsheetStatus.HUY.value: ("gray", ":material/block:"),
    CostsheetStatus.DA_THAY_THE.value: ("violet", ":material/history:"),
}
STATUS_OPTIONS = [s.value for s in CostsheetStatus]
FLAG = "🟠"
RED_FLAG = "🔴"


def status_badge(status: Any) -> None:
    label = text(status)
    color, icon = STATUS_STYLE.get(label, ("gray", ":material/info:"))
    st.badge(label, color=color, icon=icon)  # type: ignore[arg-type]


def status_column(label: str = "Trạng thái") -> Any:
    """Coloured status tag inside read-only tables (cell value = list with one status)."""
    return st.column_config.MultiselectColumn(
        label, options=STATUS_OPTIONS, color=[STATUS_STYLE[s][0] for s in STATUS_OPTIONS]
    )


def dec(value: Any) -> Decimal | None:
    """Cell / widget value -> Decimal (None stays None)."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def num(value: Any) -> float | None:
    """Decimal -> float for tables and number inputs."""
    return None if value is None else float(value)


def to_pct(value: Any) -> float | None:
    """Rate 0..1 -> percent shown on screen (x100)."""
    rate = dec(value)
    return None if rate is None else float(rate * HUNDRED)


def from_pct(value: Any) -> Decimal | None:
    """Percent typed on screen -> rate 0..1 sent to the backend."""
    percent = dec(value)
    return None if percent is None else percent / HUNDRED


def pct_text(value: Any, decimals: int = 2) -> str:
    rate = dec(value)
    return "-" if rate is None else f"{format_number(rate * HUNDRED, decimals)}%"


def enum_values(enum_cls: Iterable[Any]) -> list[str]:
    return [member.value for member in enum_cls]


def text(value: Any) -> str:
    """Enum / None -> plain text for tables and widgets."""
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def index_of(options: list[Any], value: Any) -> int | None:
    """Position of value in options (None when absent): default of a selectbox."""
    try:
        return options.index(value)
    except ValueError:
        return None


def with_value(options: Iterable[str], value: str | None) -> list[str]:
    """Options plus the stored value when it is no longer in the list (old data stays visible)."""
    result = list(dict.fromkeys(o for o in options if o))
    if value and value not in result:
        result.insert(0, value)
    return result


def text_or_empty(value: Any) -> str:
    return "" if value is None else str(value).strip()

"""Display-only number/date helpers (rounding for the screen only; the backend keeps the exact values - BR-23)."""

from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from frontend.core.formatting import format_number


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def vnd(value: Any) -> float | None:
    """VND amounts, rounded to the dong."""
    number = _num(value)
    return None if number is None else round(number, 0)


def usd(value: Any) -> float | None:
    number = _num(value)
    return None if number is None else round(number, 4)


def pct(value: Any) -> float | None:
    """Fraction -> percent number (0.015 -> 1.5)."""
    number = _num(value)
    return None if number is None else round(number * 100, 2)


def pct_exact(value: Any) -> float | None:
    """Fraction -> percent number for editable cells, without the 2-decimal display rounding (0.00395 -> 0.395).

    Only float noise is removed (0.07500000000000001 -> 7.5) so saving the table back keeps the stored value.
    """
    number = _num(value)
    return None if number is None else round(number * 100, 6)


def minutes4(value: Any) -> float | None:
    number = _num(value)
    return None if number is None else round(number, 4)


def rate2(value: Any) -> float | None:
    number = _num(value)
    return None if number is None else round(number, 2)


def plain(value: Any) -> float | None:
    """Decimal -> float for table cells without rounding."""
    return _num(value)


def fmt_date(value: date | datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%d/%m/%Y")


def yes_no(value: Any) -> str:
    return "Có" if value else "Không"


def to_decimal(value: Any) -> Decimal:
    """Cell / input value -> Decimal (empty -> 0)."""
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def optional_decimal(value: Any) -> Decimal | None:
    """Cell value -> Decimal, keeping empty cells empty (the backend reports missing values)."""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def from_percent(value: Any) -> Decimal:
    """Percent typed on screen -> fraction sent to the backend (1.5 -> 0.015)."""
    return to_decimal(value) / Decimal(100)


def pct_text(value: Any) -> str:
    """Fraction -> "12,34%" or "-"."""
    number = pct(value)
    return "-" if number is None else f"{format_number(number, 2)}%"


def percent_value(value: Any) -> float | None:
    """Value already in percent from the backend (22.27 -> 22.27), rounded to 2 decimals."""
    number = _num(value)
    return None if number is None else round(number, 2)


def percent_text(value: Any) -> str:
    """Value already in percent -> "22,27%" or "-"."""
    number = percent_value(value)
    return "-" if number is None else f"{format_number(number, 2)}%"


def count_text(value: Any) -> str:
    number = _num(value)
    if number is None:
        return "-"
    return format_number(number, 0 if number == int(number) else 2)


def components_text(components: Iterable[Any]) -> str:
    """ "Cotton 70,00% · Viscose 30,00%" from YarnComponentDTO rows (ratio as fraction)."""
    parts = []
    for c in components:
        ratio = _num(getattr(c, "ratio", None))
        label = str(getattr(c, "material_label", "") or "").strip()
        if label:
            parts.append(f"{label} {format_number(ratio * 100, 2)}%" if ratio is not None else label)
    return " · ".join(parts) or "-"


def text_or_dash(value: Any) -> str:
    return "-" if value is None or str(value).strip() == "" else str(value)

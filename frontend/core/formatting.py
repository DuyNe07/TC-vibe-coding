"""Display formatting (Vietnamese conventions). Use these instead of ad-hoc f-strings."""

from datetime import datetime
from decimal import Decimal


def format_number(value: float | int | Decimal | None, decimals: int = 0) -> str:
    """``1234567.5`` -> ``"1.234.568"`` (decimals=0) or ``"1.234.567,50"`` (decimals=2)."""
    if value is None:
        return "—"
    text = f"{float(value):,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def format_currency(value: float | int | Decimal | None, suffix: str = " ₫") -> str:
    return "—" if value is None else f"{format_number(value)}{suffix}"


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    local = value.astimezone() if value.tzinfo else value
    return local.strftime("%d/%m/%Y %H:%M")

"""BR-75 how this app writes numbers on screen: a dot before the decimals, commas between thousands (1,234,567.50)."""

from decimal import Decimal


def format_number(value: float | int | Decimal | None, decimals: int = 0) -> str:
    """``1234567.5`` -> ``"1,234,568"`` (decimals=0) or ``"1,234,567.50"`` (decimals=2); ``None`` -> ``"-"``."""
    if value is None:
        return "-"
    return f"{float(value):,.{decimals}f}"

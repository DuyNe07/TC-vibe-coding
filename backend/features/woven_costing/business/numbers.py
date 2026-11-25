"""Small Decimal helpers shared by the calculation classes (plain functions, no business decision)."""

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

ZERO = Decimal(0)
ONE = Decimal(1)


def num(value: Decimal | int | None) -> Decimal:
    """None -> 0 (an empty cell counts as 0, as in Excel)."""
    return ZERO if value is None else Decimal(value)


def div(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Division that gives 0 instead of an error when the denominator is 0 (Excel IFERROR(...; 0))."""
    return ZERO if denominator == 0 else numerator / denominator


def round_half_up(value: Decimal, digits: int = 0) -> Decimal:
    """Excel ROUND (half away from zero)."""
    return value.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)


def round_up(value: Decimal) -> Decimal:
    """Excel ROUNDUP(x; 0) for positive values."""
    return value.quantize(ONE, rounding=ROUND_CEILING)


def same_text(left: str, right: str) -> bool:
    """Excel MATCH compares text without case."""
    return left.strip().casefold() == right.strip().casefold()

"""Number helpers."""

from decimal import Decimal, InvalidOperation


def parse_decimal(value: object) -> Decimal | None:
    """Parse Excel/user input to Decimal. Returns None for empty or invalid values.

    Accepts ints, floats, and strings such as ``"1,234.5"`` or ``"1 234"``.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float):
        return Decimal(str(value))
    text = str(value).strip().replace(" ", "").replace(",", "")
    if not text:
        return None
    try:
        result = Decimal(text)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None

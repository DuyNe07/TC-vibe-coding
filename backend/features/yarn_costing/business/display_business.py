"""BR-23: rounding and Vietnamese number formatting for display and export (calculations never round)."""

from decimal import ROUND_HALF_UP, Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.constants import (
    MINUTES_DECIMALS,
    PERCENT_DECIMALS,
    RATE_DECIMALS,
    USD_DECIMALS,
    VND_DECIMALS,
)


def quantize(value: Decimal, decimals: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def format_number(value: Decimal, decimals: int) -> str:
    """Vietnamese style: 19.777,84 (dot = thousands, comma = decimals)."""
    text = f"{quantize(value, decimals):,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def format_vnd(value: Decimal) -> str:
    return format_number(value, VND_DECIMALS)


def format_usd(value: Decimal) -> str:
    return format_number(value, USD_DECIMALS)


def format_percent(ratio: Decimal) -> str:
    return format_number(ratio * 100, PERCENT_DECIMALS)


class DisplayBusiness(BaseBusiness[Decimal]):
    def round_vnd(self, value: Decimal) -> Decimal:
        """BR-23: VND làm tròn đến đồng."""
        return quantize(value, VND_DECIMALS)

    def round_usd(self, value: Decimal) -> Decimal:
        """BR-23: USD 4 chữ số thập phân."""
        return quantize(value, USD_DECIMALS)

    def round_percent(self, ratio: Decimal) -> Decimal:
        """BR-23: tỷ lệ / tiêu hao / hồi phế dạng % 2 chữ số thập phân."""
        return quantize(ratio * 100, PERCENT_DECIMALS)

    def round_minutes(self, value: Decimal) -> Decimal:
        """BR-23: thời gian 4 chữ số thập phân."""
        return quantize(value, MINUTES_DECIMALS)

    def round_rate(self, value: Decimal) -> Decimal:
        """BR-23: định mức VND/phút 2 chữ số thập phân."""
        return quantize(value, RATE_DECIMALS)

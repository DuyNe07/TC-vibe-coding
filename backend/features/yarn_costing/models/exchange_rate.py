"""4.9 Tỷ giá (Exchange rate) + 4.10 Tham số chung (Settings)."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity


class ExchangeRate(BaseEntity):
    effective_date: date
    rate: Decimal = Field(gt=0)
    note: str = Field(default="", max_length=200)
    created_by: str = ""


class CostingSettings(BaseEntity):
    trial_factor: Decimal = Field(default=Decimal(3), gt=0)
    trial_factor_effective_date: date | None = None

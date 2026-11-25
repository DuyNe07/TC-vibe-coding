"""Targets of the validation rules BR-xx (small immutable values checked by business/ rule classes)."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject


class TwistQuantity(BaseValueObject):
    """BR-21: entered Se quantity vs estimated Se output (kg)."""

    entered: Decimal
    estimated: Decimal


class Check(BaseValueObject):
    """Generic target: ``ok`` decided by the business method, ``text`` / ``items`` fill the message."""

    ok: bool
    text: str = ""
    other: str = ""
    items: list[str] = Field(default_factory=list)


class YarnPriceAge(BaseValueObject):
    """BR-44: working days between the price date and today."""

    yarn_name: str
    entered_on: date | None
    working_days: int
    valid_days: int


class CountConversion(BaseValueObject):
    """BR-81 converted count of one count text; ``value`` None when the count is not valid (BR-81 / BR-84)."""

    count: str
    value: Decimal | None = None
    error_code: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.value is not None

"""Targets of the loss group rules BR-24, BR-27, BR-28, BR-29."""

from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject


class LossGroupCheck(BaseValueObject):
    group_key: str
    factory_code: str
    duplicate: bool = False
    losses_ok: bool = True


class ComponentCheck(BaseValueObject):
    count: int
    ratio_total: Decimal
    ratios_positive: bool
    all_exist: bool
    self_or_cycle: bool
    ratio_tolerance: Decimal = Decimal("0.0001")


class LockCheck(BaseValueObject):
    group_key: str
    locked_codes: list[str] = Field(default_factory=list)
    is_so: bool = False


class DeleteCheck(BaseValueObject):
    yarn_count: int = 0
    parent_count: int = 0

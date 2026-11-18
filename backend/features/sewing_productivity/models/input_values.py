"""Values typed by the data updater, checked by BR-30, BR-39, BR-45 and BR-47 before anything is saved."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseValueObject
from backend.features.sewing_productivity.models.enums import Factory


class GoalInput(BaseValueObject):
    factory: Factory | None = None
    effective_from: date | None = None
    efficiency_target: Decimal | None = None
    mo8h_target: Decimal | None = None
    efficiency_threshold: Decimal | None = None
    mo8h_threshold: Decimal | None = None


class WeeklyChangeoverInput(BaseValueObject):
    from_date: date | None = None
    to_date: date | None = None
    counts: dict[str, int | float | None] = {}


class CatalogPair(BaseValueObject):
    key: str = ""
    value: str = ""


class CatalogInput(BaseValueObject):
    pairs: tuple[CatalogPair, ...] = ()
    lines_only: bool = False

"""UC-27 filters of the costsheet list and the KPI tiles of Screen 1."""

from datetime import date

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.enums import CostsheetStatus, DyePlant, OrderType, PriceType


class CostsheetFilter(BaseValueObject):
    keyword: str = ""
    statuses: list[CostsheetStatus] = Field(default_factory=list)
    team: str | None = None
    sales_username: str | None = None
    customer_name: str | None = None
    dye_plant: DyePlant | None = None
    order_type: OrderType | None = None
    price_type: PriceType | None = None
    date_from: date | None = None
    date_to: date | None = None
    latest_only: bool = True
    below_threshold_only: bool = False


class CostsheetKpis(BaseValueObject):
    total: int = 0
    pending: int = 0
    approved: int = 0
    closed: int = 0
    below_threshold: int = 0
    low_shrinkage: int = 0

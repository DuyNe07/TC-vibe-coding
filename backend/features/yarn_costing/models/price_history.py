"""4.15 Lịch sử giá (Price history)."""

from datetime import date, datetime

from pydantic import Field

from backend.core.base import BaseEntity, utc_now
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, PriceEvent
from backend.features.yarn_costing.models.yarn import CostBreakdown


class PriceHistory(BaseEntity):
    factory_code: FactoryCode
    yarn_code: str
    line_code: str
    line_type: LineType
    changed_at: datetime = Field(default_factory=utc_now)
    changed_by: str = ""
    event: PriceEvent
    batch_id: str | None = None
    effective_date: date | None = None
    old: CostBreakdown | None = None
    new: CostBreakdown
    reason: str = ""

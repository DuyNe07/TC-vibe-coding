"""4.16 Lần tính lại toàn bộ (Recalculation batch)."""

from datetime import date, datetime

from pydantic import Field

from backend.core.base import BaseEntity, utc_now
from backend.features.yarn_costing.models.enums import FactoryCode, PriceEvent


class RecalcBatch(BaseEntity):
    batch_code: str
    factory_code: FactoryCode
    trigger: PriceEvent
    effective_date: date
    reason: str = ""
    run_by: str = ""
    run_at: datetime = Field(default_factory=utc_now)
    yarn_count: int = 0
    changed_line_count: int = 0
    failed_yarn_count: int = 0
    line_count: int = 0

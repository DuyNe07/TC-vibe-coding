"""Results of the control checks BR-39 (giá bất thường), BR-53 (dashboard), BR-54 (NSM bất thường), BR-55."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject


class PriceAnomaly(BaseValueObject):
    factory_code: str
    technology: str
    yarn_group: str
    loss_group_key: str
    prev_code: str
    prev_count: Decimal | None
    prev_total: Decimal
    next_code: str
    next_count: Decimal | None
    next_total: Decimal
    reason: str


class NsmAnomaly(BaseValueObject):
    factory_code: str
    technology: str
    loss_group_key: str
    stage_code: str
    common_value: Decimal
    yarn_code: str
    nsm: Decimal
    reason: str = ""


class WeeklyStat(BaseValueObject):
    week_start: date
    new_requests: int = 0
    fulfilment_ratio: Decimal | None = None


class DashboardStats(BaseValueObject):
    quoted_count: int = 0
    ordered_count: int = 0
    ordered_ratio: Decimal | None = None
    new_request_count: int = 0
    fulfilment_ratio: Decimal | None = None
    waiting_count: int = 0
    weekly: list[WeeklyStat] = Field(default_factory=list)
    status_counts: dict[str, int] = Field(default_factory=dict)
    last_batch_code: str | None = None
    last_batch_up: int = 0
    last_batch_down: int = 0
    last_batch_avg_percent: Decimal | None = None


class LegacyComparison(BaseValueObject):
    yarn_code: str
    yarn_name: str = ""
    old_total: Decimal
    app_total: Decimal | None = None
    diff_vnd: Decimal | None = None
    diff_percent: Decimal | None = None
    matched: bool = False
    status: str = ""

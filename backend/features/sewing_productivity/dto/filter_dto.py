"""UC-26: filter choices and default periods."""

from datetime import date, datetime

from backend.core.base import BaseResponseDTO


class FilterOptionsResponse(BaseResponseDTO):
    """The dates are None when there is no data yet (`has_data` is False)."""

    factories: list[str]
    lines_by_factory: dict[str, list[str]]
    customer_groups: list[str]
    product_groups: list[str]
    latest_date: date | None = None
    last_upload_at: datetime | None = None
    default_week_from: date | None = None
    default_week_to: date | None = None
    default_month_from: date | None = None
    has_data: bool

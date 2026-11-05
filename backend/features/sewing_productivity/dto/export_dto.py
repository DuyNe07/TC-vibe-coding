"""UC-11, UC-12: Excel files of the weekly and daily reports."""

from datetime import date

from backend.core.base import BaseRequestDTO
from backend.features.sewing_productivity.models.enums import Factory

__all__ = ["ExportDailyRequest", "ExportWeeklyRequest", "Factory"]


class ExportWeeklyRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factories: list[Factory] = []
    customer_groups: list[str] = []
    product_groups: list[str] = []


class ExportDailyRequest(BaseRequestDTO):
    report_date: date

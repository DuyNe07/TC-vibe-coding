"""UC-07: results of one day."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.dto.overview_dto import OverviewMetricDTO
from backend.features.sewing_productivity.models.enums import Factory, RowType

__all__ = ["DailyLineRowDTO", "DailyReportRequest", "DailyReportResponse", "Factory", "OverviewMetricDTO", "RowType"]


class DailyReportRequest(BaseRequestDTO):
    report_date: date
    factory: Factory = Factory.FAC_1


class DailyLineRowDTO(BaseDTO):
    row_type: RowType
    line: str
    output: float | None = None
    cm_earning: float | None = None
    hours: float | None = None
    sewers: float | None = None
    mo: float | None = None
    mo8h: float | None = None
    mismatched_output: float | None = None
    mo8h_below: bool = False


class DailyReportResponse(BaseResponseDTO):
    metrics: list[OverviewMetricDTO]
    lines: list[DailyLineRowDTO]
    has_data: bool

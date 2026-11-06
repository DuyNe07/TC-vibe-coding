"""UC-08, UC-13: each factory day by day, with a total row."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory, RowType

__all__ = ["Factory", "MonthlyFactoryDTO", "MonthlyReportRequest", "MonthlyReportResponse", "MonthlyRowDTO", "RowType"]


class MonthlyReportRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factories: list[Factory] = []
    english: bool = False  # BR-52: English names in the Excel file


class MonthlyRowDTO(BaseDTO):
    """`work_date` is None on the total row."""

    row_type: RowType
    work_date: date | None = None
    mo: float | None = None
    hours: float | None = None
    mo8h: float | None = None
    target_b: float | None = None
    output: float | None = None
    efficiency_b: float | None = None
    target_no_ratio: float | None = None
    efficiency_no_ratio: float | None = None
    cm_earning: float | None = None
    workers: float | None = None
    efficiency_b_below: bool = False
    mo8h_below: bool = False


class MonthlyFactoryDTO(BaseDTO):
    factory: str
    rows: list[MonthlyRowDTO]


class MonthlyReportResponse(BaseResponseDTO):
    factories: list[MonthlyFactoryDTO]
    has_data: bool

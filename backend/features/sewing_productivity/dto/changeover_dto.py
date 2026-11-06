"""UC-10, UC-15: style changeovers."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory

__all__ = [
    "ChangeoverDetailDTO",
    "ChangeoverFactoryRowDTO",
    "ChangeoverLineRowDTO",
    "ChangeoverMonthRowDTO",
    "ChangeoverRequest",
    "ChangeoverResponse",
    "Factory",
]


class ChangeoverRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factories: list[Factory] = []
    lines: list[str] = []
    english: bool = False  # BR-52: English names in the Excel file


class ChangeoverFactoryRowDTO(BaseDTO):
    """On the total row (`is_total`) only the two counts have a value; every other cell is "-"."""

    factory: str
    is_total: bool = False
    kpi_count: int
    working_days: int | None = None
    line_count: int | None = None
    kpi: float | None = None
    rerun_count: int
    weekly_count: int | None = None


class ChangeoverMonthRowDTO(BaseDTO):
    month: str
    factory: str
    kpi_count: int
    working_days: int
    line_count: int
    kpi: float | None = None
    rerun_count: int


class ChangeoverLineRowDTO(BaseDTO):
    factory: str
    line: str
    kpi_count: int
    rerun_count: int


class ChangeoverDetailDTO(BaseDTO):
    work_date: date
    factory: str
    line: str
    base_po: str
    style: str
    smv: float
    cm_price: float


class ChangeoverResponse(BaseResponseDTO):
    by_factory: list[ChangeoverFactoryRowDTO]
    by_month: list[ChangeoverMonthRowDTO]
    by_line: list[ChangeoverLineRowDTO]
    details: list[ChangeoverDetailDTO]
    has_data: bool

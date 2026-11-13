"""UC-10, UC-15: style changeovers. UC-31: the same call gives the Line performance table of Screen 6."""

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
    "LinePerformanceDTO",
]


class ChangeoverRequest(BaseRequestDTO):
    """`line_performance=True`: UC-31 (Screen 6 since 2026-11-11), the line table of the first factory in `factories`;
    otherwise the changeover counts of UC-10."""

    from_date: date
    to_date: date
    factories: list[Factory] = []
    lines: list[str] = []
    english: bool = False  # BR-52: English names in the Excel file
    line_performance: bool = False


class LinePerformanceDTO(BaseDTO):
    """UC-31 one row of Screen 6 (BR-78) or the Total row (BR-79). Ratios in %; `*_below` = BR-80."""

    line: str
    is_total: bool = False
    operators: float | None = None
    target_output: float | None = None
    output: float | None = None
    output_ratio: float | None = None
    target_value: float | None = None
    value: float | None = None
    value_ratio: float | None = None
    mo8h: float | None = None
    output_ratio_below: bool = False
    mo8h_below: bool = False


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
    by_factory: list[ChangeoverFactoryRowDTO] = []
    by_month: list[ChangeoverMonthRowDTO] = []
    by_line: list[ChangeoverLineRowDTO] = []
    details: list[ChangeoverDetailDTO] = []
    has_data: bool
    line_performance: list[LinePerformanceDTO] = []  # UC-31 only

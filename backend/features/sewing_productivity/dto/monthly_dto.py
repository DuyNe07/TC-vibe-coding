"""UC-08, UC-13: each factory day by day, with a total row. UC-29: the same call with a period kind gives the
period report of Screen 4 instead (one table per figure, one row per period)."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory, PeriodKind, RowType

__all__ = [
    "CHANGEOVER_PER_LINE_DAY",
    "Factory",
    "MonthlyFactoryDTO",
    "MonthlyReportRequest",
    "MonthlyReportResponse",
    "MonthlyRowDTO",
    "PeriodCardDTO",
    "PeriodKind",
    "PeriodMetricDTO",
    "PeriodValueRowDTO",
    "RowType",
]

CHANGEOVER_PER_LINE_DAY = "Changeover/line/day"  # BR-89 (thêm 2026-11-13): a Screen 4 figure only, not on Screen 1


class MonthlyReportRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factories: list[Factory] = []
    english: bool = False  # BR-52: English names in the Excel file
    period_kind: PeriodKind | None = None  # UC-29 (BR-68); None = the day-by-day report of UC-08


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


class PeriodValueRowDTO(BaseDTO):
    """UC-29 one period: `values` and `below` (BR-28) are keyed by column (`Fac 1`... `HCM`, `Total`)."""

    period: str
    start: date
    values: dict[str, float | None]
    below: dict[str, bool]


class PeriodCardDTO(BaseDTO):
    """BR-70, BR-71 one card of Screen 4: the last period of one column and its change (None = no arrow)."""

    column: str
    value: float | None = None
    change: float | None = None
    below: bool = False


class PeriodMetricDTO(BaseDTO):
    """UC-29 one figure of BR-69 (backend name), with its BR-50 format and one row per period.

    `cards` (BR-71): one per column, compared with the days named by `compare_label` ("" = nothing to compare);
    `rising_is_good` (BR-70): True = green rise and red fall, None = the arrow is not coloured."""

    metric: str
    decimals: int
    suffix: str = ""
    rows: list[PeriodValueRowDTO]
    cards: list[PeriodCardDTO] = []
    compare_label: str = ""
    rising_is_good: bool | None = None


class MonthlyReportResponse(BaseResponseDTO):
    factories: list[MonthlyFactoryDTO]
    has_data: bool
    columns: list[str] = []  # UC-29: the chosen factories, then HCM (when shown) and Total
    period_metrics: list[PeriodMetricDTO] = []  # UC-29 only

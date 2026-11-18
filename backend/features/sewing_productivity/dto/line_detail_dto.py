"""UC-06: lines day by day, with a period row per line and the factory total."""

from datetime import date, datetime

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory, PeriodKind, RowType

__all__ = [
    "Factory",
    "FactoryDayDTO",
    "LineDetailRequest",
    "LineDetailResponse",
    "LineDetailRowDTO",
    "LineOrderDTO",
    "LineOverviewDTO",
    "LineStrengthDTO",
    "LineTrendPointDTO",
    "PeriodKind",
    "RowType",
]


class LineDetailRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factory: Factory = Factory.FAC_1
    lines: list[str] = []
    customer_groups: list[str] = []
    product_groups: list[str] = []
    # BR-90 (thêm 2026-11-13 lần 2): a line name asks for the "Line trend" of that line only (01/01 of the year of
    # `to_date` to `to_date`, cut by `trend_kind`); the other parts of the response stay empty
    trend_line: str = ""
    trend_kind: PeriodKind = PeriodKind.WEEK


class LineDetailRowDTO(BaseDTO):
    """`row_type`: one day, the line's period row or the factory total (`work_date` is None on the last two)."""

    row_type: RowType
    line: str
    work_date: date | None = None
    target_a: float | None = None
    output: float | None = None
    efficiency_a: float | None = None
    target_b: float | None = None
    efficiency_b: float | None = None
    target_no_ratio: float | None = None
    efficiency_no_ratio: float | None = None
    cm_earning: float | None = None
    sewers: float | None = None
    hours: float | None = None
    mo8h: float | None = None
    efficiency_a_below: bool = False
    efficiency_b_below: bool = False
    mo8h_below: bool = False


class FactoryDayDTO(BaseDTO):
    work_date: date
    workers: float | None = None
    hours: float | None = None


class LineOverviewDTO(BaseDTO):
    """BR-83 one row of the Line Detail table (sửa 2026-11-12) or its Total row; ratios in %."""

    line: str
    is_total: bool = False
    output: float | None = None
    efficiency: float | None = None  # %Efficiency (with ratio), thêm 2026-11-13
    mo8h: float | None = None
    hours: float | None = None
    matching_ratio: float | None = None
    changeover: int = 0
    efficiency_below: bool = False
    mo8h_below: bool = False


class LineOrderDTO(BaseDTO):
    """BR-84 one base order a line made in the chosen dates. `matches` None = "-"."""

    line: str
    base_po: str
    customers: str
    styles: str
    product_types: str
    cm_price: float | None = None
    output: float
    smv: float | None = None  # BR-88 (thêm 2026-11-13)
    efficiency: float | None = None  # BR-88 %Efficiency (with ratio) of the order (thêm 2026-11-13)
    first_day: date | None = None
    matches: bool | None = None


class LineStrengthDTO(BaseDTO):
    """Section 4.11 one line of the Line Strength file (BR-81)."""

    factory: str
    line: str
    strong_groups: list[str] = []
    buyers: str = ""
    changeover_speed: str = ""
    remark: str = ""
    file_name: str = ""
    updated_at: datetime | None = None


class LineTrendPointDTO(BaseDTO):
    """BR-90 one period of the "Line trend": ratios in %; `*_below` = BR-28 against the level of its last day."""

    period: str
    start: date
    output: float | None = None
    efficiency: float | None = None
    mo8h: float | None = None
    efficiency_below: bool = False
    mo8h_below: bool = False


class LineDetailResponse(BaseResponseDTO):
    rows: list[LineDetailRowDTO]
    factory_days: list[FactoryDayDTO]
    note: str = ""
    has_data: bool
    line_overview: list[LineOverviewDTO] = []  # BR-83 (sửa 2026-11-12)
    line_orders: list[LineOrderDTO] = []  # BR-84, every line of the table
    strengths: list[LineStrengthDTO] = []  # BR-84, the lines of the chosen factory that have one
    trend: list[LineTrendPointDTO] = []  # BR-90, only when the request names a `trend_line`

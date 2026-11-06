"""UC-06: lines day by day, with a period row per line and the factory total."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory, RowType

__all__ = ["Factory", "FactoryDayDTO", "LineDetailRequest", "LineDetailResponse", "LineDetailRowDTO", "RowType"]


class LineDetailRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factory: Factory = Factory.FAC_1
    lines: list[str] = []
    customer_groups: list[str] = []
    product_groups: list[str] = []


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


class LineDetailResponse(BaseResponseDTO):
    rows: list[LineDetailRowDTO]
    factory_days: list[FactoryDayDTO]
    note: str = ""
    has_data: bool

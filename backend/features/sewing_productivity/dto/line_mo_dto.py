"""UC-09, UC-14: the 5 tables of one factory, lines in rows and days in columns."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory

__all__ = ["Factory", "LineMoCellDTO", "LineMoRequest", "LineMoResponse", "LineMoRowDTO", "LineMoTableDTO"]


class LineMoRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factory: Factory = Factory.FAC_1
    lines: list[str] = []
    english: bool = False  # BR-52: English names in the Excel file


class LineMoCellDTO(BaseDTO):
    value: float | None = None
    below: bool = False


class LineMoRowDTO(BaseDTO):
    """`cells` holds only the days the line worked; a day that is missing is shown as "-"."""

    line: str
    is_total: bool = False
    cells: dict[date, LineMoCellDTO]
    period: LineMoCellDTO


class LineMoTableDTO(BaseDTO):
    title: str
    decimals: int
    suffix: str = ""
    rows: list[LineMoRowDTO]


class LineMoResponse(BaseResponseDTO):
    dates: list[date]
    tables: list[LineMoTableDTO]
    has_data: bool
    no_ratio_table: LineMoTableDTO | None = None  # BR-55, the last tab

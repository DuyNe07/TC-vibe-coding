"""Screen 5 -> response DTO, and its Excel file (UC-14)."""

from datetime import date

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.builders.display import (
    KIND_DECIMALS,
    NOT_AVAILABLE,
    as_float,
    excel_date,
    excel_value,
    is_below,
    suffix_of,
    with_header,
)
from backend.features.sewing_productivity.constants import PERIOD_LABEL
from backend.features.sewing_productivity.dto.line_mo_dto import (
    LineMoCellDTO,
    LineMoResponse,
    LineMoRowDTO,
    LineMoTableDTO,
)
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.report_values import MatrixCell, MatrixTable
from backend.shared.file_io import ExcelWriter


def _cell(cell: MatrixCell) -> LineMoCellDTO:
    return LineMoCellDTO(value=as_float(cell.value), below=is_below(cell.assessment))


class LineMoResponseBuilder(BaseBuilder[LineMoResponse]):
    def __init__(self, dates: list[date], tables: list[MatrixTable], has_data: bool) -> None:
        self.dates = dates
        self.tables = tables
        self.has_data = has_data

    def build(self) -> LineMoResponse:
        return LineMoResponse(
            dates=self.dates,
            tables=[
                LineMoTableDTO(
                    title=table.title,
                    decimals=KIND_DECIMALS[table.kind],
                    suffix=suffix_of(table.kind),
                    rows=[
                        LineMoRowDTO(
                            line=row.line,
                            is_total=row.is_total,
                            cells={day: _cell(cell) for day, cell in row.cells.items()},
                            period=_cell(row.period),
                        )
                        for row in table.rows
                    ],
                )
                for table in self.tables
            ],
            has_data=self.has_data,
        )


class LineMoFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(
        self, factory: Factory, from_date: date, to_date: date, dates: list[date], tables: list[MatrixTable]
    ) -> None:
        self.factory = factory
        self.from_date = from_date
        self.to_date = to_date
        self.dates = dates
        self.tables = tables

    def build(self) -> FileDownloadDTO:
        headers = ("Chuyền", *(excel_date(day) for day in self.dates), PERIOD_LABEL)
        sheets = {table.sheet: with_header(self._rows(table), headers) for table in self.tables}
        return FileDownloadDTO(
            filename=f"mo-theo-chuyen_{self.factory.value}_{self.from_date.isoformat()}_{self.to_date.isoformat()}.xlsx",
            content=ExcelWriter().write(sheets),
            mime_type=MimeType.XLSX,
        )

    def _rows(self, table: MatrixTable) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for row in table.rows:
            values: dict[str, object] = {"Chuyền": row.line}
            for day in self.dates:
                cell = row.cells.get(day)
                values[excel_date(day)] = excel_value(cell.value, table.kind) if cell else NOT_AVAILABLE
            values[PERIOD_LABEL] = excel_value(row.period.value, table.kind)
            rows.append(values)
        return rows

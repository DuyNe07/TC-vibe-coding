"""BR-85 the Excel file of Screen 6 Line performance (UC-32), in the layout of the user's line report: one sheet per
factory (sửa 2026-11-13), each with a two-level header, one row per line, the Total row. Numbers, never formulas."""

from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.models.enums import Assessment, Factory
from backend.features.sewing_productivity.models.report_values import LinePerformance

NO_DATA = "No data in this period."
HEADER_FILL = PatternFill("solid", fgColor="D3F4FD")
TOTAL_FILL = PatternFill("solid", fgColor="FFFFCC")
BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14)
THIN = Side(style="thin", color="999999")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
INTEGER = "#,##0"
MONEY = "#,##0.00"
PEOPLE = "#,##0.0"
PERCENT = "0.0%"
HUNDRED = Decimal(100)
FIRST_DATA_ROW = 4
# (top header, sub header, field, number format); a top header spanning several columns is repeated
COLUMNS = (
    ("Line", "", "line", ""),
    ("Number of Operators", "", "operators", PEOPLE),
    ("Production Output (pcs)", "Target", "target_output", INTEGER),
    ("Production Output (pcs)", "Actual", "output", INTEGER),
    ("Production Output (pcs)", "ratio", "output_ratio", PERCENT),
    ("Production Value ($)", "Target", "target_value", MONEY),
    ("Production Value ($)", "Actual", "value", MONEY),
    ("Production Value ($)", "ratio", "value_ratio", PERCENT),
    ("MO $\n(Convert to 8h)", "", "mo8h", MONEY),
    ("Below threshold", "", "below", ""),
)
COLUMN_WIDTHS = (14, 12, 12, 12, 10, 14, 14, 10, 14, 22)


class LinePerformanceFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(self, from_date: date, to_date: date, by_factory: dict[Factory, list[LinePerformance]]) -> None:
        """`by_factory`: the rows of every factory, in the fixed factory order (sửa 2026-11-13: one sheet each)."""
        self.from_date = from_date
        self.to_date = to_date
        self.by_factory = by_factory

    def build(self) -> FileDownloadDTO:
        book = Workbook()
        book.remove(book.active)
        days = f"{self.from_date:%d.%m} to {self.to_date:%d.%m}"
        for factory, rows in self.by_factory.items():
            self._sheet(book.create_sheet(english_name(factory.value)), english_name(factory.value), days, rows)
        stream = BytesIO()
        book.save(stream)
        return FileDownloadDTO(
            filename=f"Line performance - {days}.xlsx", content=stream.getvalue(), mime_type=MimeType.XLSX
        )

    def _sheet(self, sheet: Worksheet, name: str, days: str, rows: list[LinePerformance]) -> None:
        """One factory: the title, the two-level header, one row per line and the Total row."""
        sheet.cell(row=1, column=1, value=f"Line performance - {name} ({days})").font = TITLE
        self._header(sheet)
        if not rows:
            sheet.cell(row=FIRST_DATA_ROW, column=1, value=NO_DATA)
        for offset, row in enumerate(rows):
            self._line(sheet, FIRST_DATA_ROW + offset, row)
        for index, width in enumerate(COLUMN_WIDTHS, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width
        sheet.freeze_panes = sheet.cell(row=FIRST_DATA_ROW, column=2)

    @staticmethod
    def _header(sheet: Worksheet) -> None:
        """Rows 2-3: a column alone spans both rows; Output and Value span 3 columns over Target / Actual / ratio."""
        column = 1
        while column <= len(COLUMNS):
            top, sub, _field, _format = COLUMNS[column - 1]
            span = sum(1 for item in COLUMNS if item[0] == top)
            for offset in range(span):
                for header_row in (2, 3):
                    cell = sheet.cell(row=header_row, column=column + offset)
                    cell.fill, cell.font, cell.alignment, cell.border = HEADER_FILL, BOLD, CENTER, BOX
            sheet.cell(row=2, column=column, value=top)
            if sub:
                for offset in range(span):
                    sheet.cell(row=3, column=column + offset, value=COLUMNS[column - 1 + offset][1])
                sheet.merge_cells(start_row=2, start_column=column, end_row=2, end_column=column + span - 1)
            else:
                sheet.merge_cells(start_row=2, start_column=column, end_row=3, end_column=column)
            column += span

    @staticmethod
    def _value(row: LinePerformance, field: str) -> Any:
        if field == "line":
            return english_name(row.line)
        if field == "below":
            below = [
                label
                for label, assessment in (("Output ratio", row.output_ratio_assessment), ("MO 8h", row.mo8h_assessment))
                if assessment == Assessment.BELOW
            ]
            return ", ".join(below)
        value = getattr(row, field)
        if value is None:
            return "-"
        return float(value / HUNDRED) if field.endswith("ratio") else float(value)

    def _line(self, sheet: Worksheet, excel_row: int, row: LinePerformance) -> None:
        for index, (_top, _sub, field, number_format) in enumerate(COLUMNS, start=1):
            cell = sheet.cell(row=excel_row, column=index, value=self._value(row, field))
            cell.border = BOX
            if number_format:
                cell.number_format = number_format
            if row.is_total:
                cell.font, cell.fill = BOLD, TOTAL_FILL

"""BR-64 the weekly report in the layout of the weekly meeting workbook: sheet Overall and one sheet per factory.

The layout copies `Sewing - Weekly Fac report - <dd.mm> to <dd.mm>.xlsx` (colours, merged titles, $ and % formats).
openpyxl is used directly: the shared ExcelWriter writes plain tables only. Cells hold numbers, never formulas."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.constants import ALL_FACTORIES, HCM_COLUMN, WORKER_COLUMNS
from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.models.enums import RowType
from backend.features.sewing_productivity.models.report_values import FactoryDetail, FactorySummary

NOT_AVAILABLE = "-"
HUNDRED = Decimal(100)
CATEGORY_FILL = PatternFill("solid", fgColor="FFFF99")
LABEL_FILL = PatternFill("solid", fgColor="FFFFCC")
HEADER_FILL = PatternFill("solid", fgColor="D3F4FD")
DATE_FILL = PatternFill("solid", fgColor="FDEEE7")
BLOCK_FILL = PatternFill("solid", fgColor="0070C0")
BOLD = Font(bold=True)
RED = Font(color="FF0000")
TITLE = Font(bold=True, color="FF0000", size=16)
WHITE_BOLD = Font(bold=True, color="FFFFFF")
THIN = Side(style="thin", color="A6A6A6")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
PIECES = "#,##0"
MONEY = '"$"#,##0'
MONEY_2 = '"$"#,##0.00'
PERCENT = "0%"
PERCENT_1 = "0.0%"
DECIMAL_2 = "0.00"
FACTORY_CODES = {factory: code for code, factory in WORKER_COLUMNS.items()}  # Fac 2 -> SF2, Fac 1 -> SFVL


def _number(value: Decimal | int | None, percent: bool = False) -> float | str:
    """A cell: the exact number (Excel shows it with the format of the cell), "-" when there is none."""
    if value is None:
        return NOT_AVAILABLE
    return float(Decimal(value) / HUNDRED) if percent else float(value)


def _put(ws: Worksheet, row: int, column: int, value: Any, number_format: str = "", **style: Any) -> None:
    cell = ws.cell(row=row, column=column, value=value)
    cell.border = BOX
    if number_format:
        cell.number_format = number_format
    for name, item in style.items():
        setattr(cell, name, item)


def _label(
    ws: Worksheet, row: int, column: int, text: str, fill: PatternFill, end_row: int = 0, end_col: int = 0
) -> None:
    _put(ws, row, column, text, fill=fill, font=BOLD, alignment=CENTER)
    if end_row or end_col:
        for r in range(row, (end_row or row) + 1):
            for c in range(column, (end_col or column) + 1):
                ws.cell(row=r, column=c).border = BOX
        ws.merge_cells(start_row=row, start_column=column, end_row=end_row or row, end_column=end_col or column)


class MeetingReportFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(
        self, from_date: date, to_date: date, summaries: Sequence[FactorySummary], details: Sequence[FactoryDetail]
    ) -> None:
        self.from_date = from_date
        self.to_date = to_date
        self.summaries = {summary.column: summary for summary in summaries}
        self.details = details

    @property
    def period(self) -> str:
        return f"{self.from_date:%d.%m} to {self.to_date:%d.%m}"

    def build(self) -> FileDownloadDTO:
        book = Workbook()
        self._overall(book.active)
        for detail in self.details:
            self._detail(book.create_sheet(f"{english_name(detail.factory.value)}-detailed"), detail)
        buffer = BytesIO()
        book.save(buffer)
        return FileDownloadDTO(
            filename=f"Sewing - Weekly Fac report - {self.period}.xlsx",
            content=buffer.getvalue(),
            mime_type=MimeType.XLSX,
        )

    # ---- sheet Overall ----
    def _overall(self, ws: Worksheet) -> None:
        ws.title = "Overall"
        columns = [*(factory.value for factory in ALL_FACTORIES), HCM_COLUMN]  # BR-98
        last = 2 + len(columns)
        ws.cell(row=1, column=1, value=f"Sewing Weekly performance ({self.period})").font = TITLE
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last)
        ws.cell(row=1, column=1).alignment = CENTER
        _label(ws, 2, 1, "Category", HEADER_FILL, end_col=2)
        for index, column in enumerate(columns, start=3):
            _label(ws, 2, index, english_name(column), HEADER_FILL)
        groups: list[tuple[str, list[tuple[str, str, str, bool, bool]]]] = [
            # category, [(sub-label, summary field, format, is percent, red)]
            ("Efficiency", [("Target", "target_a", PIECES, False, False), ("Actual", "output", PIECES, False, False)]),
            (
                "Efficiency",
                [
                    ("Target", "efficiency_target", PERCENT, True, False),
                    ("Actual", "efficiency_a", PERCENT_1, True, False),
                    ("%", "efficiency_a_vs_target", PERCENT, True, True),
                ],
            ),
            ("CM earning", [("Actual", "cm_earning", MONEY, False, False)]),
            (
                "MO 8h",
                [
                    ("Target", "mo8h_target", MONEY, False, False),
                    ("Actual", "mo8h", MONEY_2, False, False),
                    ("%", "mo8h_vs_target", PERCENT_1, True, True),
                ],
            ),
        ]
        row = 3
        for category, items in groups:
            _label(ws, row, 1, category, CATEGORY_FILL, end_row=row + len(items) - 1)
            for sub_label, field, number_format, percent, red in items:
                _label(ws, row, 2, sub_label, LABEL_FILL)
                for index, column in enumerate(columns, start=3):
                    value = (
                        _number(getattr(self.summaries[column], field, None), percent)
                        if column in self.summaries
                        else NOT_AVAILABLE
                    )
                    style = {"font": RED, "fill": LABEL_FILL} if red else {}
                    _put(ws, row, index, value, number_format, alignment=Alignment(horizontal="right"), **style)
                row += 1
        singles = [
            ("Average CM price", "average_cm_price", MONEY_2, False, CATEGORY_FILL),
            ("Avg working time", "average_hours", DECIMAL_2, False, HEADER_FILL),
            ("Matching ratio", "strength_match", PERCENT, True, HEADER_FILL),
            ("Changeover time", "weekly_changeover", PIECES, False, HEADER_FILL),
            ("", "weekly_changeover_per_line", DECIMAL_2, False, HEADER_FILL),
        ]
        for text, field, number_format, percent, fill in singles:
            _label(ws, row, 1, text, fill, end_col=2)
            for index, column in enumerate(columns, start=3):
                value = (
                    _number(getattr(self.summaries[column], field, None), percent)
                    if column in self.summaries
                    else NOT_AVAILABLE
                )
                _put(ws, row, index, value, number_format, alignment=Alignment(horizontal="right"))
            row += 1
        ws.column_dimensions["A"].width = 18
        ws.column_dimensions["B"].width = 10
        for index in range(3, last + 1):
            ws.column_dimensions[get_column_letter(index)].width = 15

    # ---- sheets <factory>-detailed ----
    def _detail(self, ws: Worksheet, detail: FactoryDetail) -> None:
        code = FACTORY_CODES.get(detail.factory, detail.factory.value)
        _label(ws, 1, 1, "Start of week", HEADER_FILL, end_col=3)
        for index, text in enumerate(("Day", "Month", "Year"), start=1):
            _label(ws, 2, index, text, DATE_FILL)
        for index, value in enumerate((self.from_date.day, self.from_date.month, self.from_date.year), start=1):
            _put(ws, 3, index, value, fill=LABEL_FILL, alignment=CENTER)

        dates = sorted({stat.day for stat in detail.lines if stat.day} | {stat.day for stat in detail.days if stat.day})
        names = list(dict.fromkeys(stat.line for stat in detail.lines))
        by_line_day = {(stat.line, stat.day): stat for stat in detail.lines if stat.row_type == RowType.DAY}
        period = {stat.line: stat for stat in detail.lines if stat.row_type == RowType.PERIOD}
        day_stats = {stat.day: stat for stat in detail.days}

        end_output = self._output_block(ws, code, dates, names, by_line_day, period, day_stats, detail.summary)
        end_earning = self._matrix_block(
            ws, end_output + 2, code, "Earning ($)", dates, names, by_line_day, period, day_stats, detail.summary,
            "cm_earning", MONEY, labour=True,
        )  # fmt: skip
        self._matrix_block(
            ws, end_earning + 2, code, "MO 8h ($/8h)", dates, names, by_line_day, period, day_stats, detail.summary,
            "mo8h", MONEY_2, labour=False,
        )  # fmt: skip
        ws.column_dimensions["A"].width = 12

    def _output_block(
        self,
        ws: Worksheet,
        code: str,
        dates: list[date],
        names: list[str],
        by_line_day: dict,
        period: dict,
        day_stats: dict,
        summary: FactorySummary,
    ) -> int:
        """Output (pcs): per day Target / Actual / Efficiency, then Target, Total, Efficiency of the period."""
        last = 1 + 3 * len(dates) + 3
        _label(ws, 5, 1, "Output (pcs)", HEADER_FILL, end_col=last)
        _label(ws, 6, 1, code, HEADER_FILL, end_row=7)
        for index, day in enumerate(dates):
            column = 2 + 3 * index
            _put(ws, 6, column, day, "dd/mm/yyyy", font=BOLD, fill=HEADER_FILL, alignment=CENTER)
            for c in range(column, column + 3):
                ws.cell(row=6, column=c).border = BOX
            ws.merge_cells(start_row=6, start_column=column, end_row=6, end_column=column + 2)
            for offset, text in enumerate(("Target", "Actual", "Efficiency")):
                _label(ws, 7, column + offset, text, LABEL_FILL)
        for offset, text in enumerate(("Target", "Total", "Efficiency")):
            _label(ws, 6, last - 2 + offset, text, HEADER_FILL, end_row=7)
        row = 8
        for line in names:
            _put(ws, row, 1, line, font=BOLD)
            for index, day in enumerate(dates):
                stat = by_line_day.get((line, day))
                column = 2 + 3 * index
                _put(ws, row, column, _number(stat.target_a) if stat else NOT_AVAILABLE, PIECES)
                _put(ws, row, column + 1, _number(stat.output) if stat else NOT_AVAILABLE, PIECES)
                _put(ws, row, column + 2, _number(stat.efficiency_a, True) if stat else NOT_AVAILABLE, PERCENT)
            stat = period.get(line)
            _put(ws, row, last - 2, _number(stat.target_a) if stat else NOT_AVAILABLE, PIECES)
            _put(ws, row, last - 1, _number(stat.output) if stat else NOT_AVAILABLE, PIECES)
            _put(ws, row, last, _number(stat.efficiency_a, True) if stat else NOT_AVAILABLE, PERCENT)
            row += 1
        _put(ws, row, 1, "Total", font=BOLD, fill=LABEL_FILL)
        _put(ws, row + 1, 1, "MO 8h", font=BOLD)
        for index, day in enumerate(dates):
            stat = day_stats.get(day)
            column = 2 + 3 * index
            _put(ws, row, column, _number(stat.target_a) if stat else NOT_AVAILABLE, PIECES, font=BOLD, fill=LABEL_FILL)
            _put(
                ws, row, column + 1, _number(stat.output) if stat else NOT_AVAILABLE, PIECES, font=BOLD, fill=LABEL_FILL
            )
            efficiency = _number(stat.efficiency_a, True) if stat else NOT_AVAILABLE
            _put(ws, row, column + 2, efficiency, PERCENT, font=BOLD, fill=LABEL_FILL)
            _put(ws, row + 1, column + 2, _number(stat.mo8h) if stat else NOT_AVAILABLE, MONEY_2)
        _put(ws, row, last - 2, _number(summary.target_a), PIECES, font=BOLD, fill=LABEL_FILL)
        _put(ws, row, last - 1, _number(summary.output), PIECES, font=BOLD, fill=LABEL_FILL)
        _put(ws, row, last, _number(summary.efficiency_a, True), PERCENT, font=BOLD, fill=LABEL_FILL)
        _put(ws, row + 1, last, _number(summary.mo8h), MONEY_2)
        for index in range(2, last + 1):
            ws.column_dimensions[get_column_letter(index)].width = 11
        return last

    def _matrix_block(
        self,
        ws: Worksheet,
        start: int,
        code: str,
        title: str,
        dates: list[date],
        names: list[str],
        by_line_day: dict,
        period: dict,
        day_stats: dict,
        summary: FactorySummary,
        field: str,
        number_format: str,
        labour: bool,
    ) -> int:
        """Earning ($) or MO 8h ($/8h): lines in rows, days in columns, a Total column and a Total row."""
        last = start + len(dates) + 1
        _put(ws, 3, start, code, font=BOLD)
        _label(ws, 3, start + 1, title, BLOCK_FILL, end_col=last)
        ws.cell(row=3, column=start + 1).font = WHITE_BOLD
        for index, day in enumerate(dates, start=start + 1):
            _put(ws, 4, index, day, "dd/mm/yyyy", font=BOLD, fill=HEADER_FILL, alignment=CENTER)
            _label(ws, 5, index, "Actual", LABEL_FILL)
        _label(ws, 4, last, "Total", HEADER_FILL, end_row=5)
        row = 6
        for line in names:
            _put(ws, row, start, line, font=BOLD)
            for index, day in enumerate(dates, start=start + 1):
                stat = by_line_day.get((line, day))
                _put(ws, row, index, _number(getattr(stat, field)) if stat else NOT_AVAILABLE, number_format)
            stat = period.get(line)
            _put(ws, row, last, _number(getattr(stat, field)) if stat else NOT_AVAILABLE, number_format, font=BOLD)
            row += 1
        _put(ws, row, start, "Total", font=BOLD, fill=LABEL_FILL)
        for index, day in enumerate(dates, start=start + 1):
            stat = day_stats.get(day)
            _put(
                ws,
                row,
                index,
                _number(getattr(stat, field)) if stat else NOT_AVAILABLE,
                number_format,
                font=BOLD,
                fill=LABEL_FILL,
            )
        _put(ws, row, last, _number(getattr(summary, field)), number_format, font=BOLD, fill=LABEL_FILL)
        if labour:
            _put(ws, row + 1, start, "LABOR", font=BOLD)
            _put(ws, row + 2, start, "HOUR", font=BOLD)
            workers = [
                day_stats[day].workers for day in dates if day in day_stats and day_stats[day].workers is not None
            ]
            for index, day in enumerate(dates, start=start + 1):
                stat = day_stats.get(day)
                _put(ws, row + 1, index, _number(stat.workers) if stat else NOT_AVAILABLE, PIECES)
                _put(ws, row + 2, index, _number(stat.hours) if stat else NOT_AVAILABLE, DECIMAL_2)
            _put(ws, row + 1, last, float(sum(workers)) if workers else NOT_AVAILABLE, PIECES)
            _put(ws, row + 2, last, _number(summary.average_hours), DECIMAL_2)
        ws.column_dimensions[get_column_letter(start)].width = 12
        for index in range(start + 1, last + 1):
            ws.column_dimensions[get_column_letter(index)].width = 12
        return last

"""Screen 2 -> response DTO, and the weekly Excel file (UC-11)."""

from datetime import date

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.builders.display import (
    as_float,
    excel_date,
    excel_value,
    is_below,
    with_header,
)
from backend.features.sewing_productivity.builders.overview_builders import ASSESSMENT_ROWS, OVERVIEW_ROWS
from backend.features.sewing_productivity.constants import PERIOD_LABEL
from backend.features.sewing_productivity.dto.line_detail_dto import (
    FactoryDayDTO,
    LineDetailResponse,
    LineDetailRowDTO,
)
from backend.features.sewing_productivity.models.enums import NumberKind
from backend.features.sewing_productivity.models.report_values import FactoryDayStat, FactorySummary, LineStat
from backend.shared.file_io import ExcelWriter

WEEKLY_LINE_HEADERS = (
    "Chuyền", "Ngày", "Mục tiêu A", "Sản lượng", "Hiệu suất A (%)", "Mục tiêu B", "Hiệu suất B (%)", "Tiền CM",
    "Số người", "Giờ làm", "MO 8h", "Đánh giá hiệu suất A", "Đánh giá hiệu suất B", "Đánh giá MO 8h",
)  # fmt: skip


class LineDetailResponseBuilder(BaseBuilder[LineDetailResponse]):
    def __init__(self, rows: list[LineStat], days: list[FactoryDayStat], note: str, has_data: bool) -> None:
        self.rows = rows
        self.days = days
        self.note = note
        self.has_data = has_data

    def build(self) -> LineDetailResponse:
        return LineDetailResponse(
            rows=[self._row(stat) for stat in self.rows],
            factory_days=[
                FactoryDayDTO(work_date=stat.day, workers=as_float(stat.workers), hours=as_float(stat.hours))
                for stat in self.days
            ],
            note=self.note,
            has_data=self.has_data,
        )

    @staticmethod
    def _row(stat: LineStat) -> LineDetailRowDTO:
        return LineDetailRowDTO(
            row_type=stat.row_type,
            line=stat.line,
            work_date=stat.day,
            target_a=as_float(stat.target_a),
            output=as_float(stat.output),
            efficiency_a=as_float(stat.efficiency_a),
            target_b=as_float(stat.target_b),
            efficiency_b=as_float(stat.efficiency_b),
            cm_earning=as_float(stat.cm_earning),
            sewers=as_float(stat.sewers),
            hours=as_float(stat.hours),
            mo8h=as_float(stat.mo8h),
            efficiency_a_below=is_below(stat.efficiency_a_assessment),
            efficiency_b_below=is_below(stat.efficiency_b_assessment),
            mo8h_below=is_below(stat.mo8h_assessment),
        )


class WeeklyReportFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(
        self, from_date: date, to_date: date, summaries: list[FactorySummary], lines: dict[str, list[LineStat]]
    ) -> None:
        self.from_date = from_date
        self.to_date = to_date
        self.summaries = summaries
        self.lines = lines

    def build(self) -> FileDownloadDTO:
        sheets: dict[str, list[dict[str, object]]] = {"Tong quan": self._overview()}
        for factory, stats in self.lines.items():
            sheets[factory] = with_header([self._line_row(stat) for stat in stats], WEEKLY_LINE_HEADERS)
        return FileDownloadDTO(
            filename=f"bao-cao-tuan_{self.from_date.isoformat()}_{self.to_date.isoformat()}.xlsx",
            content=ExcelWriter().write(sheets),
            mime_type=MimeType.XLSX,
        )

    def _overview(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = [
            {
                "Chỉ số": label,
                **{summary.factory.value: excel_value(getattr(summary, field), kind) for summary in self.summaries},
            }
            for label, field, kind, _assessment in OVERVIEW_ROWS
        ]
        rows.extend(
            {"Chỉ số": label, **{summary.factory.value: getattr(summary, field).value for summary in self.summaries}}
            for label, field in ASSESSMENT_ROWS
        )
        return rows

    @staticmethod
    def _line_row(stat: LineStat) -> dict[str, object]:
        return {
            "Chuyền": stat.line,
            "Ngày": excel_date(stat.day, PERIOD_LABEL),
            "Mục tiêu A": excel_value(stat.target_a, NumberKind.INTEGER),
            "Sản lượng": excel_value(stat.output, NumberKind.INTEGER),
            "Hiệu suất A (%)": excel_value(stat.efficiency_a, NumberKind.PERCENT),
            "Mục tiêu B": excel_value(stat.target_b, NumberKind.INTEGER),
            "Hiệu suất B (%)": excel_value(stat.efficiency_b, NumberKind.PERCENT),
            "Tiền CM": excel_value(stat.cm_earning, NumberKind.MONEY),
            "Số người": excel_value(stat.sewers, NumberKind.PEOPLE),
            "Giờ làm": excel_value(stat.hours, NumberKind.MONEY),
            "MO 8h": excel_value(stat.mo8h, NumberKind.MONEY),
            "Đánh giá hiệu suất A": stat.efficiency_a_assessment.value,
            "Đánh giá hiệu suất B": stat.efficiency_b_assessment.value,
            "Đánh giá MO 8h": stat.mo8h_assessment.value,
        }

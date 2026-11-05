"""Screen 3 -> response DTO, and its Excel file (UC-12)."""

from datetime import date

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.builders.display import as_float, excel_value, is_below, with_header
from backend.features.sewing_productivity.builders.overview_builders import ASSESSMENT_ROWS, DAILY_ROWS, metric_rows
from backend.features.sewing_productivity.dto.daily_dto import DailyLineRowDTO, DailyReportResponse
from backend.features.sewing_productivity.models.enums import NumberKind
from backend.features.sewing_productivity.models.report_values import DailyFactorySummary, LineStat
from backend.shared.file_io import ExcelWriter

DAILY_LINE_HEADERS = (
    "Xưởng", "Chuyền", "Sản lượng", "Tiền CM", "Giờ làm", "Số người", "MO", "MO 8h", "Sản lượng trái sở trường",
    "Đánh giá MO 8h",
)  # fmt: skip


class DailyReportResponseBuilder(BaseBuilder[DailyReportResponse]):
    def __init__(self, summaries: list[DailyFactorySummary], lines: list[LineStat], has_data: bool) -> None:
        self.summaries = summaries
        self.lines = lines
        self.has_data = has_data

    def build(self) -> DailyReportResponse:
        return DailyReportResponse(
            metrics=metric_rows(DAILY_ROWS, self.summaries),
            lines=[
                DailyLineRowDTO(
                    row_type=stat.row_type,
                    line=stat.line,
                    output=as_float(stat.output),
                    cm_earning=as_float(stat.cm_earning),
                    hours=as_float(stat.hours),
                    sewers=as_float(stat.sewers),
                    mo=as_float(stat.mo),
                    mo8h=as_float(stat.mo8h),
                    mismatched_output=as_float(stat.mismatched_output),
                    mo8h_below=is_below(stat.mo8h_assessment),
                )
                for stat in self.lines
            ],
            has_data=self.has_data,
        )


class DailyReportFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(self, report_date: date, summaries: list[DailyFactorySummary], lines: list[LineStat]) -> None:
        self.report_date = report_date
        self.summaries = summaries
        self.lines = lines

    def build(self) -> FileDownloadDTO:
        factories: list[dict[str, object]] = [
            {
                "Chỉ số": label,
                **{summary.factory.value: excel_value(getattr(summary, field), kind) for summary in self.summaries},
            }
            for label, field, kind, _assessment in DAILY_ROWS
        ]
        factories.extend(
            {"Chỉ số": label, **{summary.factory.value: getattr(summary, field).value for summary in self.summaries}}
            for label, field in ASSESSMENT_ROWS
        )
        sheets = {
            "Xuong": factories,
            "Chuyen": with_header([self._line_row(stat) for stat in self.lines], DAILY_LINE_HEADERS),
        }
        return FileDownloadDTO(
            filename=f"bao-cao-ngay_{self.report_date.isoformat()}.xlsx",
            content=ExcelWriter().write(sheets),
            mime_type=MimeType.XLSX,
        )

    @staticmethod
    def _line_row(stat: LineStat) -> dict[str, object]:
        return {
            "Xưởng": stat.factory.value,
            "Chuyền": stat.line,
            "Sản lượng": excel_value(stat.output, NumberKind.INTEGER),
            "Tiền CM": excel_value(stat.cm_earning, NumberKind.MONEY),
            "Giờ làm": excel_value(stat.hours, NumberKind.MONEY),
            "Số người": excel_value(stat.sewers, NumberKind.PEOPLE),
            "MO": excel_value(stat.mo, NumberKind.MONEY),
            "MO 8h": excel_value(stat.mo8h, NumberKind.MONEY),
            "Sản lượng trái sở trường": excel_value(stat.mismatched_output, NumberKind.INTEGER),
            "Đánh giá MO 8h": stat.mo8h_assessment.value,
        }

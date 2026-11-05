"""Screen 4 -> response DTO, and its Excel file (UC-13)."""

from datetime import date

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.builders.display import (
    as_float,
    excel_date,
    excel_value,
    is_below,
    with_header,
)
from backend.features.sewing_productivity.constants import TOTAL_LINE_LABEL
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyFactoryDTO, MonthlyReportResponse, MonthlyRowDTO
from backend.features.sewing_productivity.models.enums import NumberKind, RowType
from backend.features.sewing_productivity.models.report_values import FactoryDayStat
from backend.shared.file_io import ExcelWriter

MONTHLY_HEADERS = (
    "Ngày", "MO", "Giờ làm", "MO 8h", "Mục tiêu B", "Sản lượng", "Hiệu suất B (%)", "Tiền CM", "Số thợ",
    "Đánh giá hiệu suất B", "Đánh giá MO 8h",
)  # fmt: skip


class MonthlyReportResponseBuilder(BaseBuilder[MonthlyReportResponse]):
    def __init__(self, tables: dict[str, list[FactoryDayStat]], has_data: bool) -> None:
        self.tables = tables
        self.has_data = has_data

    def build(self) -> MonthlyReportResponse:
        return MonthlyReportResponse(
            factories=[
                MonthlyFactoryDTO(factory=factory, rows=[self._row(stat) for stat in stats])
                for factory, stats in self.tables.items()
            ],
            has_data=self.has_data,
        )

    @staticmethod
    def _row(stat: FactoryDayStat) -> MonthlyRowDTO:
        return MonthlyRowDTO(
            row_type=RowType.DAY if stat.day else RowType.TOTAL,
            work_date=stat.day,
            mo=as_float(stat.mo),
            hours=as_float(stat.hours),
            mo8h=as_float(stat.mo8h),
            target_b=as_float(stat.target_b),
            output=as_float(stat.output),
            efficiency_b=as_float(stat.efficiency_b),
            cm_earning=as_float(stat.cm_earning),
            workers=as_float(stat.workers),
            efficiency_b_below=is_below(stat.efficiency_b_assessment),
            mo8h_below=is_below(stat.mo8h_assessment),
        )


class MonthlyReportFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(self, from_date: date, to_date: date, tables: dict[str, list[FactoryDayStat]]) -> None:
        self.from_date = from_date
        self.to_date = to_date
        self.tables = tables

    def build(self) -> FileDownloadDTO:
        sheets = {
            factory: with_header([self._row(stat) for stat in stats], MONTHLY_HEADERS)
            for factory, stats in self.tables.items()
        }
        return FileDownloadDTO(
            filename=f"bao-cao-thang_{self.from_date.isoformat()}_{self.to_date.isoformat()}.xlsx",
            content=ExcelWriter().write(sheets),
            mime_type=MimeType.XLSX,
        )

    @staticmethod
    def _row(stat: FactoryDayStat) -> dict[str, object]:
        return {
            "Ngày": excel_date(stat.day, TOTAL_LINE_LABEL),
            "MO": excel_value(stat.mo, NumberKind.MONEY),
            "Giờ làm": excel_value(stat.hours, NumberKind.MONEY),
            "MO 8h": excel_value(stat.mo8h, NumberKind.MONEY),
            "Mục tiêu B": excel_value(stat.target_b, NumberKind.INTEGER),
            "Sản lượng": excel_value(stat.output, NumberKind.INTEGER),
            "Hiệu suất B (%)": excel_value(stat.efficiency_b, NumberKind.PERCENT),
            "Tiền CM": excel_value(stat.cm_earning, NumberKind.MONEY),
            "Số thợ": excel_value(stat.workers, NumberKind.PEOPLE),
            "Đánh giá hiệu suất B": stat.efficiency_b_assessment.value,
            "Đánh giá MO 8h": stat.mo8h_assessment.value,
        }

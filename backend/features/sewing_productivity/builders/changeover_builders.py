"""Screen 6 -> response DTO, and its Excel file (UC-15)."""

from datetime import date

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.sewing_productivity.builders.display import (
    NOT_AVAILABLE,
    as_float,
    excel_date,
    excel_value,
    with_header,
)
from backend.features.sewing_productivity.constants import TOTAL_LINE_LABEL
from backend.features.sewing_productivity.dto.changeover_dto import (
    ChangeoverDetailDTO,
    ChangeoverFactoryRowDTO,
    ChangeoverLineRowDTO,
    ChangeoverMonthRowDTO,
    ChangeoverResponse,
)
from backend.features.sewing_productivity.models.enums import NumberKind
from backend.features.sewing_productivity.models.report_values import ChangeoverReport
from backend.shared.file_io import ExcelWriter

FACTORY_HEADERS = (
    "Xưởng", "Số lần đổi KPI", "Số ngày làm việc", "Số chuyền", "KPI đổi mã hàng", "Số lần đổi gồm cả lên lại",
    "Đổi mã hàng tuần",
)  # fmt: skip
MONTH_HEADERS = (
    "Tháng", "Xưởng", "Số lần đổi KPI", "Số ngày làm việc", "Số chuyền", "KPI đổi mã hàng", "Số lần đổi gồm cả lên lại",
)  # fmt: skip
LINE_HEADERS = ("Xưởng", "Chuyền", "Số lần đổi KPI", "Số lần đổi gồm cả lên lại")
DETAIL_HEADERS = ("Ngày", "Xưởng", "Chuyền", "Mã đơn gốc", "Style", "SMV", "Giá CM")


class ChangeoverResponseBuilder(BaseBuilder[ChangeoverResponse]):
    def __init__(self, report: ChangeoverReport) -> None:
        self.report = report

    def build(self) -> ChangeoverResponse:
        report = self.report
        factory_rows = [
            ChangeoverFactoryRowDTO(
                factory=count.factory.value,
                kpi_count=count.kpi_count,
                working_days=count.working_days,
                line_count=count.line_count,
                kpi=as_float(count.kpi),
                rerun_count=count.rerun_count,
                weekly_count=count.weekly_count,
            )
            for count in report.by_factory
        ]
        if factory_rows:
            factory_rows.append(
                ChangeoverFactoryRowDTO(
                    factory=TOTAL_LINE_LABEL,
                    is_total=True,
                    kpi_count=report.total_kpi_count,
                    rerun_count=report.total_rerun_count,
                )
            )
        return ChangeoverResponse(
            by_factory=factory_rows,
            by_month=[
                ChangeoverMonthRowDTO(
                    month=count.month,
                    factory=count.factory.value,
                    kpi_count=count.kpi_count,
                    working_days=count.working_days,
                    line_count=count.line_count,
                    kpi=as_float(count.kpi),
                    rerun_count=count.rerun_count,
                )
                for count in report.by_month
            ],
            by_line=[
                ChangeoverLineRowDTO(
                    factory=count.factory.value,
                    line=count.line,
                    kpi_count=count.kpi_count,
                    rerun_count=count.rerun_count,
                )
                for count in report.by_line
            ],
            details=[
                ChangeoverDetailDTO(
                    work_date=item.day,
                    factory=item.factory.value,
                    line=item.line,
                    base_po=item.base_po,
                    style=item.style,
                    smv=float(item.smv),
                    cm_price=float(item.cm_price),
                )
                for item in report.details
            ],
            has_data=report.has_data,
        )


class ChangeoverFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(self, from_date: date, to_date: date, report: ChangeoverReport) -> None:
        self.from_date = from_date
        self.to_date = to_date
        self.report = report

    def build(self) -> FileDownloadDTO:
        sheets = {
            "Theo xuong": with_header(self._factory_rows(), FACTORY_HEADERS),
            "Theo thang": with_header(self._month_rows(), MONTH_HEADERS),
            "Theo chuyen": with_header(self._line_rows(), LINE_HEADERS),
            "Chi tiet": with_header(self._detail_rows(), DETAIL_HEADERS),
        }
        return FileDownloadDTO(
            filename=f"doi-ma-hang_{self.from_date.isoformat()}_{self.to_date.isoformat()}.xlsx",
            content=ExcelWriter().write(sheets),
            mime_type=MimeType.XLSX,
        )

    def _factory_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = [
            {
                "Xưởng": count.factory.value,
                "Số lần đổi KPI": count.kpi_count,
                "Số ngày làm việc": count.working_days,
                "Số chuyền": count.line_count,
                "KPI đổi mã hàng": excel_value(count.kpi, NumberKind.KPI),
                "Số lần đổi gồm cả lên lại": count.rerun_count,
                "Đổi mã hàng tuần": NOT_AVAILABLE if count.weekly_count is None else count.weekly_count,
            }
            for count in self.report.by_factory
        ]
        if rows:
            rows.append(
                {
                    "Xưởng": TOTAL_LINE_LABEL,
                    "Số lần đổi KPI": self.report.total_kpi_count,
                    "Số ngày làm việc": NOT_AVAILABLE,
                    "Số chuyền": NOT_AVAILABLE,
                    "KPI đổi mã hàng": NOT_AVAILABLE,
                    "Số lần đổi gồm cả lên lại": self.report.total_rerun_count,
                    "Đổi mã hàng tuần": NOT_AVAILABLE,
                }
            )
        return rows

    def _month_rows(self) -> list[dict[str, object]]:
        return [
            {
                "Tháng": count.month,
                "Xưởng": count.factory.value,
                "Số lần đổi KPI": count.kpi_count,
                "Số ngày làm việc": count.working_days,
                "Số chuyền": count.line_count,
                "KPI đổi mã hàng": excel_value(count.kpi, NumberKind.KPI),
                "Số lần đổi gồm cả lên lại": count.rerun_count,
            }
            for count in self.report.by_month
        ]

    def _line_rows(self) -> list[dict[str, object]]:
        return [
            {
                "Xưởng": count.factory.value,
                "Chuyền": count.line,
                "Số lần đổi KPI": count.kpi_count,
                "Số lần đổi gồm cả lên lại": count.rerun_count,
            }
            for count in self.report.by_line
        ]

    def _detail_rows(self) -> list[dict[str, object]]:
        return [
            {
                "Ngày": excel_date(item.day),
                "Xưởng": item.factory.value,
                "Chuyền": item.line,
                "Mã đơn gốc": item.base_po,
                "Style": item.style,
                "SMV": excel_value(item.smv, NumberKind.MONEY),
                "Giá CM": excel_value(item.cm_price, NumberKind.MONEY),
            }
            for item in self.report.details
        ]

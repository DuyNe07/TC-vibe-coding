"""Generated Excel files: 5.4 bảng giá, 5.5 đối chiếu giá cũ / chênh lệch tính lại / kết quả nhập file."""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.yarn_costing.constants import MINUTES_DECIMALS, PERCENT_DECIMALS, RATE_DECIMALS, USD_DECIMALS
from backend.features.yarn_costing.dto.import_dto import LegacyComparisonRowDTO, RejectedRowDTO, SheetResultDTO
from backend.features.yarn_costing.dto.master_dto import RecalcDiffRowDTO
from backend.features.yarn_costing.dto.price_dto import PriceLineRowDTO
from backend.features.yarn_costing.dto.pricing_dto import StageCostDTO
from backend.shared.file_io import ExcelWriter


def rnd(value: Decimal | None, decimals: int = 0) -> float | int | None:
    """BR-23 rounding for files: VND to the đồng, USD 4 decimals, % 2 decimals."""
    if value is None:
        return None
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    return int(rounded) if decimals == 0 else float(rounded)


def pct(ratio: Decimal | None) -> float | None:
    return rnd(ratio * 100, PERCENT_DECIMALS) if ratio is not None else None  # type: ignore[return-value]


def xlsx(filename: str, sheets: dict[str, list[dict]]) -> FileDownloadDTO:
    return FileDownloadDTO(filename=filename, content=ExcelWriter().write(sheets), mime_type=MimeType.XLSX)


class PriceExportFileBuilder(BaseBuilder[FileDownloadDTO]):
    """UC-29: sheets 'Bang gia' and 'Chi tiet cong doan' (5.4)."""

    def __init__(
        self, rows: list[PriceLineRowDTO], details: list[tuple[str, str, StageCostDTO]], now: datetime
    ) -> None:
        self.rows, self.details, self.now = rows, details, now

    def build(self) -> FileDownloadDTO:
        price_rows = [
            {
                "STT": r.stt,
                "Xưởng": r.factory_code.value,
                "Mã dòng": r.line_code,
                "Loại dòng": r.line_type.value,
                "Mã gốc": r.base_code,
                "Tên sợi": r.yarn_name,
                "Nhóm sợi": r.yarn_group,
                "Chi số": float(r.count) if r.count is not None else None,
                "Công nghệ": r.technology.value,
                "Nhóm tiêu hao": r.loss_group_key,
                "Thành phần": r.components_text,
                "Nhân công": rnd(r.labor),
                "Khấu hao": rnd(r.depreciation),
                "Điện": rnd(r.electricity),
                "Vật tư": rnd(r.materials),
                "CPQL": rnd(r.overhead),
                "Tổng (VND/kg)": rnd(r.total_vnd),
                "USD/kg": rnd(r.usd_per_kg, USD_DECIMALS),
                "Tỷ giá": rnd(r.exchange_rate),
                "Loại đóng gói": r.packaging_code,
                "Tên loại đóng gói": r.packaging_name,
                "Ngày tính giá": r.first_priced_at.strftime("%d/%m/%Y") if r.first_priced_at else None,
                "Ngày hiệu lực": r.effective_date.strftime("%d/%m/%Y") if r.effective_date else None,
                "Trạng thái": r.status.value,
                "Mã kế toán": r.accounting_code,
                "% CK/PP": pct(r.adjustment_percent),
                "Lý do CK/PP": r.adjustment_reason,
                "Đơn hàng": r.order_ref,
            }
            for r in self.rows
        ]
        detail_rows = [
            {
                "Mã tính giá": code,
                "Tên sợi": name,
                "STT": d.sequence,
                "Công đoạn": d.stage_code,
                "Tên công đoạn": d.stage_name,
                "Nguyên liệu": d.material_label,
                "Lượt": d.pass_no,
                "NSM (kg/giờ)": float(d.nsm) if d.nsm is not None else None,
                "Thời gian chạy máy (phút/kg)": rnd(d.run_minutes, MINUTES_DECIMALS),
                "Tiêu hao": pct(d.loss),
                "Tiêu hao lũy kế": pct(d.cumulative_loss),
                "Định mức (VND/phút)": rnd(d.total_rate, RATE_DECIMALS),
                "Chi phí/kg": rnd(d.cost_per_kg),
                "Nhân công": rnd(d.labor),
                "Khấu hao": rnd(d.depreciation),
                "Điện": rnd(d.electricity),
                "Vật tư": rnd(d.materials),
                "CPQL": rnd(d.overhead),
                "Ghi chú tiêu hao": d.loss_note,
            }
            for code, name, d in self.details
        ]
        filename = f"bang-gia-soi-{self.now.strftime('%Y%m%d-%H%M')}.xlsx"
        return xlsx(filename, {"Bang gia": price_rows, "Chi tiet cong doan": detail_rows})


class LegacyComparisonFileBuilder(BaseBuilder[FileDownloadDTO]):
    """5.5 doi-chieu-gia-cu-<yyyymmdd>.xlsx."""

    def __init__(self, rows: list[LegacyComparisonRowDTO], now: datetime) -> None:
        self.rows, self.now = rows, now

    def build(self) -> FileDownloadDTO:
        data = [
            {
                "Mã": r.yarn_code,
                "Tên sợi": r.yarn_name,
                "Tổng giá cũ": rnd(r.old_total),
                "Tổng giá app": rnd(r.app_total),
                "Chênh lệch (VND)": rnd(r.diff_vnd),
                "Chênh lệch (%)": rnd(r.diff_percent, PERCENT_DECIMALS),
                "Nhân công cũ": rnd(r.old_labor),
                "Khấu hao cũ": rnd(r.old_depreciation),
                "Điện cũ": rnd(r.old_electricity),
                "Vật tư cũ": rnd(r.old_materials),
                "CPQL cũ": rnd(r.old_overhead),
                "Nhân công mới": rnd(r.new_labor),
                "Khấu hao mới": rnd(r.new_depreciation),
                "Điện mới": rnd(r.new_electricity),
                "Vật tư mới": rnd(r.new_materials),
                "CPQL mới": rnd(r.new_overhead),
                "Trạng thái": r.status,
            }
            for r in self.rows
        ]
        return xlsx(f"doi-chieu-gia-cu-{self.now.strftime('%Y%m%d')}.xlsx", {"Doi chieu": data})


class RecalcDiffFileBuilder(BaseBuilder[FileDownloadDTO]):
    """5.5 chenh-lech-tinh-lai-<batch_id>.xlsx."""

    def __init__(self, batch_id: str, rows: list[RecalcDiffRowDTO]) -> None:
        self.batch_id, self.rows = batch_id, rows

    def build(self) -> FileDownloadDTO:
        data = [
            {
                "Mã dòng": r.line_code,
                "Tên sợi": r.yarn_name,
                "Loại dòng": r.line_type.value,
                "Tổng trước": rnd(r.old_total),
                "Tổng sau": rnd(r.new_total),
                "Chênh lệch (VND)": rnd(r.diff_vnd),
                "Chênh lệch (%)": rnd(r.diff_percent, PERCENT_DECIMALS),
            }
            for r in self.rows
        ]
        return xlsx(f"chenh-lech-tinh-lai-{self.batch_id}.xlsx", {"Chenh lech": data})


class ImportResultFileBuilder(BaseBuilder[FileDownloadDTO]):
    """5.5 ket-qua-nhap-file-<import_id>.xlsx: Sheet; Dòng Excel; Mã / nhóm; Kết quả; Lý do."""

    def __init__(self, import_id: str, sheets: list[SheetResultDTO], rejected: list[RejectedRowDTO]) -> None:
        self.import_id, self.sheets, self.rejected = import_id, sheets, rejected

    def build(self) -> FileDownloadDTO:
        rows = [
            {
                "Sheet": s.sheet,
                "Dòng Excel": None,
                "Mã / nhóm": "(tổng)",
                "Kết quả": f"Tạo {s.created} / Cập nhật {s.updated} / Bị loại {s.rejected}",
                "Lý do": s.skipped_message,
            }
            for s in self.sheets
        ]
        rows += [
            {"Sheet": r.sheet, "Dòng Excel": r.excel_row, "Mã / nhóm": r.key, "Kết quả": "Bị loại", "Lý do": r.reason}
            for r in self.rejected
        ]
        return xlsx(f"ket-qua-nhap-file-{self.import_id}.xlsx", {"Ket qua": rows})

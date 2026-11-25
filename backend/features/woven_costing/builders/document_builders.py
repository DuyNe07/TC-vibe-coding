"""Generated files: F-07 fabric labels (Word) and F-08 costsheet list (Excel)."""

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.woven_costing.dto.list_dto import CostsheetListRowDTO
from backend.features.woven_costing.models.label import FabricLabel
from backend.shared.file_io import ExcelWriter, WordContent, WordWriter

LABEL_COLUMNS = 2
LIST_SHEET = "Costsheet"


def label_text(label: FabricLabel) -> str:
    """One label as in sheet PRINT."""
    lines = [
        f"TCFNO: {label.tcfno}",
        f"FABRIC: {label.fabric_name}",
        "YARN SPEC:",
        *[f"  {line}" for line in label.yarn_lines],
        f"WIDTH: {label.width_cm} CM / {label.width_inch} INCH" if label.width_cm else "WIDTH:",
        f"WEIGHT: {label.gsm} G/M2 / {label.g_per_m} G/MT" if label.gsm or label.g_per_m else "WEIGHT:",
        f"DENSITY: WARP {label.warp_density} / WEFT {label.weft_density} (/10 CM)"
        if label.warp_density or label.weft_density
        else "DENSITY:",
        f"REMARK: {label.remark}",
    ]
    return "\n".join(lines)


class LabelDocumentBuilder(BaseBuilder[FileDownloadDTO]):
    """F-07: up to 4 labels on one page (2 columns x 2 rows), file nhan-<first tcfno>.docx."""

    def __init__(self, labels: list[FabricLabel]) -> None:
        self.labels = labels

    def build(self) -> FileDownloadDTO:
        texts = [label_text(label) for label in self.labels]
        while len(texts) % LABEL_COLUMNS:
            texts.append("")
        rows = [texts[i : i + LABEL_COLUMNS] for i in range(0, len(texts), LABEL_COLUMNS)]
        content = WordContent().add_table(rows[0], rows[1:])
        first = self.labels[0].tcfno if self.labels else "vai"
        return FileDownloadDTO(
            filename=f"nhan-{first}.docx", content=WordWriter().write(content), mime_type=MimeType.DOCX
        )


class CostsheetExportBuilder(BaseBuilder[FileDownloadDTO]):
    """F-08: the columns of Screen 1 for the filtered rows, sheet "Costsheet"."""

    def __init__(self, rows: list[CostsheetListRowDTO], file_name: str) -> None:
        self.rows = rows
        self.file_name = file_name

    def build(self) -> FileDownloadDTO:
        data = [
            {
                "Số costsheet": r.costsheet_no,
                "Phiên bản": r.version,
                "Trạng thái": r.status.value,
                "Ngày tính giá": r.costing_date,
                "Sales": r.sales_name,
                "Team": r.team,
                "Khách hàng": r.customer_name,
                "Thị trường": r.market.value if r.market else "",
                "Loại đơn": r.order_type.value if r.order_type else "",
                "OC": r.oc_no,
                "Mã vải": r.tcfno,
                "Hình thức bán": r.sale_form.value if r.sale_form else "",
                "Nhà máy nhuộm": r.dye_plant.value,
                "Loại giá": r.price_type.value if r.price_type else "",
                "Số mét": float(r.order_meters or 0),
                "Giá bán (VND/m)": round(float(r.sell_price_vnd), 0),
                "Giá bán (USD/m)": round(float(r.sell_price_usd), 4),
                "Giá vốn (VND/m)": round(float(r.cogs_vnd), 0),
                "F&I (VND/m)": round(float(r.freight_insurance), 0),
                "GP%": round(float(r.gp_pct) * 100, 2),
                "OP%": round(float(r.op_pct) * 100, 2),
                "Cảnh báo": r.warning_text,
                "Người duyệt": r.approved_by_name,
                "Ngày duyệt": r.approved_at.replace(tzinfo=None) if r.approved_at else None,
            }
            for r in self.rows
        ]
        if not data:
            data = [dict.fromkeys(EXPORT_COLUMNS)]
        return FileDownloadDTO(filename=self.file_name, content=ExcelWriter().write({LIST_SHEET: data}),
                               mime_type=MimeType.XLSX)  # fmt: skip


EXPORT_COLUMNS = (
    "Số costsheet", "Phiên bản", "Trạng thái", "Ngày tính giá", "Sales", "Team", "Khách hàng", "Thị trường",
    "Loại đơn", "OC", "Mã vải", "Hình thức bán", "Nhà máy nhuộm", "Loại giá", "Số mét", "Giá bán (VND/m)",
    "Giá bán (USD/m)", "Giá vốn (VND/m)", "F&I (VND/m)", "GP%", "OP%", "Cảnh báo", "Người duyệt", "Ngày duyệt",
)  # fmt: skip

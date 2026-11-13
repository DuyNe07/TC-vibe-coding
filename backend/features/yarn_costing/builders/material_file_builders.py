"""Đợt 2 (bổ sung 2026-11-10): 5.10 đọc file kho tháng, 5.11 đọc file hàng sắp về, 5.12 xuất danh sách giá báo khách."""

from typing import Any

from backend.core.base import BaseBuilder, FileDownloadDTO, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.yarn_costing.builders.file_builders import pct, rnd, xlsx
from backend.features.yarn_costing.constants import HEADER_SCAN_ROWS, MAX_SHEET_ROWS, USD_DECIMALS
from backend.features.yarn_costing.dto.material_dto import QuoteDTO
from backend.features.yarn_costing.exceptions import ImportFileError
from backend.features.yarn_costing.models.material_price import ParsedRows
from backend.shared.file_io.excel import ExcelReader
from backend.shared.utils.text import normalize_key

MSG_FILE = "Không đọc được file '{name}'. Hãy kiểm tra lại file Excel."
MSG_TOO_BIG = "File phải là .xlsx, .xlsm hoặc .xls, không quá 60 MB và mỗi sheet không quá 10.000 dòng."
MSG_MISSING = "File thiếu cột bắt buộc: {columns}."
MSG_SHEET_MISSING = "Sheet '{sheet}' thiếu cột bắt buộc: {columns}."
MSG_NO_ARRIVAL_SHEET = "File không có sheet 'Update Fiber arrival ...'."
ARRIVAL_SHEET_PREFIX = "update fiber arrival"

# 5.10: field → accepted header labels (normalize_key form) + label shown when missing
STOCK_COLUMNS: dict[str, tuple[tuple[str, ...], str]] = {
    "ica": (("ica name",), "ICA_NAME"),
    "code": (("itt code",), "ITT_CODE"),
    "name": (("vat tu",), "VAT_TU"),
    "unit": (("dvt",), "DVT"),
    "opening_qty": (("sl ton",), "SL_TON"),
    "opening_value": (("gt ton",), "GT_TON"),
    "in_qty": (("sl nhap",), "SL_NHAP"),
    "in_value": (("gt nhap",), "GT_NHAP"),
    "out_qty": (("sl xuat",), "SL_XUAT"),
    "out_value": (("gt xuat",), "GT_XUAT"),
    "closing_qty": (("sl cuoi",), "SL_CUOI"),
    "closing_value": (("gt cuoi1", "gt cuoi"), "GT_CUOI1 hoặc GT_CUOI"),
}
STOCK_OPTIONAL = {"period": ("cf ape date",)}

# 5.11
ARRIVAL_REQUIRED = {
    "supplier": (("supplier",), "SUPPLIER"),
    "description": (("type",), "TYPE"),
    "quantity": (("quantity in kg",), "Quantity in kg"),
    "unit_price": (("unit price",), "Unit price"),
    "eta_warehouse": (("eta at warehouse",), "ETA AT WAREHOUSE"),
    "warehouse": (("warehouse",), "WAREHOUSE"),
}
ARRIVAL_OPTIONAL = {
    "commodity": ("good description", "commodity"),
    "spec": ("spec",),
    "contract_no": ("no", "contract no"),
    "contract_date": ("date",),
    "term": ("term",),
    "origin_country": ("country of origin",),
    "shipment_date": ("shipment date",),
    "eta_port": ("eta at port",),
    "note": ("note",),
    "receiving_price": ("gia nhap kho",),
}


def _read(file: UploadedFileDTO, sheet: str | int) -> list[dict[str, Any]]:
    try:
        return ExcelReader(sheet_name=sheet, max_rows=MAX_SHEET_ROWS).read(file)
    except FileProcessingError as exc:
        raise ImportFileError(MSG_TOO_BIG if "rows" in str(exc) else MSG_FILE.format(name=file.filename)) from exc
    except Exception as exc:
        raise ImportFileError(MSG_FILE.format(name=file.filename)) from exc


def _match(labels: dict[str, str], wanted: dict[str, tuple[str, ...]]) -> dict[str, str]:
    """column key → field, for the columns whose (normalized) label is one of the accepted labels of a field."""
    found: dict[str, str] = {}
    for field, accepted in wanted.items():
        for key, label in labels.items():
            if key not in found and normalize_key(label) in accepted:
                found[key] = field
                break
    return found


class StockFileReaderBuilder(BaseBuilder[ParsedRows]):
    """5.10: first sheet, header on row 1."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> ParsedRows:
        records = _read(self.file, 0)
        labels = {key: key for key in (records[0] if records else {})}
        mapping = _match(labels, {f: accepted for f, (accepted, _) in STOCK_COLUMNS.items()})
        missing = [label for f, (_, label) in STOCK_COLUMNS.items() if f not in mapping.values()]
        if missing:
            return ParsedRows(problem=MSG_MISSING.format(columns=", ".join(missing)))
        period_key = next(iter(_match(labels, STOCK_OPTIONAL)), None)
        period_text = next((str(r[period_key]) for r in records if period_key and r.get(period_key)), "")
        rows = [
            (index + 2, {field: row.get(key) for key, field in mapping.items()}) for index, row in enumerate(records)
        ]
        return ParsedRows(sheet="", rows=rows, period_text=period_text)


class ArrivalFileReaderBuilder(BaseBuilder[ParsedRows]):
    """5.11: sheet 'Update Fiber arrival ...', header in 1 or 2 rows found among the first rows (row with SUPPLIER)."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> ParsedRows:
        try:
            names = ExcelReader().sheet_names(self.file)
        except Exception as exc:
            raise ImportFileError(MSG_FILE.format(name=self.file.filename)) from exc
        sheet = next((n for n in names if normalize_key(n).startswith(ARRIVAL_SHEET_PREFIX)), None)
        if sheet is None:
            raise ImportFileError(MSG_NO_ARRIVAL_SHEET)
        records = _read(self.file, sheet)
        candidates = [({k: k for k in records[0]} if records else {}, -1)]
        candidates += [(row, index) for index, row in enumerate(records[:HEADER_SCAN_ROWS])]
        header_index = next(
            (index for cells, index in candidates if any(normalize_key(v) == "supplier" for v in cells.values())), None
        )
        if header_index is None:
            return ParsedRows(
                sheet=sheet,
                problem=MSG_SHEET_MISSING.format(
                    sheet=sheet, columns=", ".join(label for _, label in ARRIVAL_REQUIRED.values())
                ),
            )
        upper = {k: k for k in records[0]} if header_index == -1 else records[header_index]
        lower = records[header_index + 1] if header_index + 1 < len(records) else {}
        # a column takes the label of the row below when it has one (two-row header), else the label above
        labels_low = {k: str(v) for k, v in lower.items() if v is not None and str(v).strip()}
        labels_up = {k: str(v) for k, v in upper.items() if v is not None and str(v).strip()}
        wanted = {f: accepted for f, (accepted, _) in ARRIVAL_REQUIRED.items()} | ARRIVAL_OPTIONAL
        mapping = _match(labels_low, wanted)
        rest = {f: a for f, a in wanted.items() if f not in mapping.values()}
        mapping |= _match({k: v for k, v in labels_up.items() if k not in mapping}, rest)
        missing = [label for f, (_, label) in ARRIVAL_REQUIRED.items() if f not in mapping.values()]
        if missing:
            return ParsedRows(sheet=sheet, problem=MSG_SHEET_MISSING.format(sheet=sheet, columns=", ".join(missing)))
        first_data = header_index + (2 if labels_low and any(k in labels_low for k in mapping) else 1)
        rows = [
            (index + 2, {field: row.get(key) for key, field in mapping.items()})
            for index, row in enumerate(records)
            if index >= first_data
        ]
        return ParsedRows(sheet=sheet, rows=rows)


class QuoteExportFileBuilder(BaseBuilder[FileDownloadDTO]):
    """5.12 sheet 'Gia bao khach'."""

    def __init__(self, quotes: list[QuoteDTO], filename: str) -> None:
        self.quotes, self.filename = quotes, filename

    def build(self) -> FileDownloadDTO:
        rows = []
        for q in self.quotes:
            parts = "; ".join(
                f"{c.material_label} {pct(c.ratio)}% · {c.price_group} {rnd(c.net_usd, USD_DECIMALS)}"
                for c in q.components
            )
            rows.append(
                {
                    "Số báo giá": q.quote_no,
                    "Tháng": q.period,
                    "Ngày tính": q.created_at.strftime("%d/%m/%Y") if q.created_at else "",
                    "Người tính": q.created_by,
                    "Khách hàng": q.customer_name,
                    "Mã dòng": q.line_code,
                    "Tên chuẩn": q.yarn_name,
                    "Mã kế toán": q.accounting_code,
                    "Thường / Thí nghiệm": q.price_kind.value,
                    "Nội địa / Xuất khẩu": q.market.value,
                    "SL đơn (kg)": rnd(q.order_qty, 2),
                    "Tỷ giá": rnd(q.exchange_rate),
                    "Giá NL (USD/kg)": rnd(q.material_usd, USD_DECIMALS),
                    "Norm (USD/kg)": rnd(q.norm_usd, USD_DECIMALS),
                    "Hệ số": pct(q.norm_factor),
                    "Giá vốn mới (USD/kg)": rnd(q.new_cost_usd, USD_DECIMALS),
                    "SL sợi tồn (kg)": rnd(q.stock_qty, 2),
                    "Giá vốn sợi tồn (USD/kg)": rnd(q.stock_cost_usd, USD_DECIMALS),
                    "Giá vốn BQ (USD/kg)": rnd(q.avg_cost_usd, USD_DECIMALS),
                    "GP %": pct(q.gp_percent),
                    "Commission %": pct(q.commission_percent),
                    "FOB / CIF": q.incoterm.value,
                    "F&I (USD/kg)": rnd(q.fi_usd, USD_DECIMALS),
                    "Giá FOB (USD/kg)": rnd(q.fob_usd, USD_DECIMALS),
                    "Giá CIF (USD/kg)": rnd(q.cif_usd, USD_DECIMALS),
                    "Giá FOB (VND/kg)": rnd(q.fob_usd * q.exchange_rate),
                    "Giá CIF (VND/kg)": rnd(q.cif_usd * q.exchange_rate) if q.cif_usd is not None else None,
                    "Thành phần": parts,
                    # bổ sung 2026-11-13 (BR-110, BR-111)
                    "Tỷ lệ Supima": pct(q.supima_percent),
                    "Truyền điểm coin": "Có" if q.supima_coin else "Không",
                    "Phí coin (USD/kg)": rnd(q.coin_fee_usd, USD_DECIMALS),
                    "Phương án bông": " + ".join(f"{s.origin.value} {pct(s.percent)}%" for s in q.cotton_plan),
                    "Ghi chú": q.note,
                }
            )
        return xlsx(self.filename, {"Gia bao khach": rows})

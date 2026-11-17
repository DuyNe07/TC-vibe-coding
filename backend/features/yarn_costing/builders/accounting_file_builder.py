"""5.9 File giá thành kế toán (file Z, UC-53, bổ sung 2026-11-10): every month sheet → rows keyed by field name.

The header is not on row 1 (title, blank row, then 'STT | MÃ | TÊN SẢN PHẨM ...'), so each sheet is read once with the
shared ExcelReader and the header row is found among the first rows by its cell values."""

from collections.abc import Callable
from typing import Any

from backend.core.base import BaseBuilder, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.yarn_costing.constants import HEADER_SCAN_ROWS, MAX_SHEET_ROWS
from backend.features.yarn_costing.exceptions import ImportFileError
from backend.features.yarn_costing.models.accounting_cost import ZSheet
from backend.shared.file_io.excel import ExcelReader
from backend.shared.utils.text import normalize_key

COLUMNS = {
    "code": "MÃ",
    "name": "TÊN SẢN PHẨM",
    "quantity": "SỐ LƯỢNG",
    "vlc": "VLC",
    "labor": "NHÂN CÔNG + BẢO TRÌ",
    "depreciation": "KHẤU HAO",
    "power": "ĐỘNG LỰC",
    "materials": "VẬT TƯ, NHIÊN LIỆU, CCDC, VẬT LIỆU PHỤ",
    "overhead": "CHI PHÍ QUẢN LÝ",
    "total": "CỘNG",
}
MSG_FILE = "Không đọc được file '{name}'. Hãy kiểm tra lại file Excel."
MSG_TOO_BIG = "File phải là .xlsx, .xlsm hoặc .xls, không quá 60 MB và mỗi sheet không quá 10.000 dòng."
MSG_NO_SHEET = "File không có sheet giá thành dạng 'Z SỢI Txx.yy'."
MSG_MISSING = "Sheet '{sheet}' thiếu cột bắt buộc: {columns}."


def _header_map(cells: dict[str, Any]) -> dict[str, str]:
    """column key of the reader → field name, when the cells hold the header labels."""
    wanted = {normalize_key(label): field for field, label in COLUMNS.items()}
    found: dict[str, str] = {}
    for key, value in cells.items():
        field = wanted.get(normalize_key(value))
        if field and field not in found.values():
            found[key] = field
    return found


class AccountingFileReaderBuilder(BaseBuilder[list[ZSheet]]):
    def __init__(self, file: UploadedFileDTO, period_of: Callable[[str], str | None]) -> None:
        """``period_of(sheet name)`` → 'yyyy-mm', '' (month unreadable) or None (not a Z sheet) - BR-80."""
        self.file, self.period_of = file, period_of

    def _records(self, sheet: str) -> list[dict[str, Any]]:
        try:
            return ExcelReader(sheet_name=sheet, max_rows=MAX_SHEET_ROWS).read(self.file)
        except FileProcessingError as exc:
            raise ImportFileError(
                MSG_TOO_BIG if "rows" in str(exc) else MSG_FILE.format(name=self.file.filename)
            ) from exc
        except Exception as exc:
            raise ImportFileError(MSG_FILE.format(name=self.file.filename)) from exc

    def _sheet(self, sheet: str, period: str) -> ZSheet:
        records = self._records(sheet)
        # the reader's first row is the header of pandas: the real header is either those keys or one of the rows
        candidates = [({k: k for k in records[0]} if records else {}, -1)]
        candidates += [(row, index) for index, row in enumerate(records[:HEADER_SCAN_ROWS])]
        best: tuple[dict[str, str], int] = ({}, -1)
        for cells, index in candidates:
            mapping = _header_map(cells)
            if len(mapping) > len(best[0]):
                best = (mapping, index)
        mapping, header_index = best
        missing = [label for field, label in COLUMNS.items() if field not in mapping.values()]
        if missing:
            return ZSheet(
                sheet=sheet, period=period, problem=MSG_MISSING.format(sheet=sheet, columns=", ".join(missing))
            )
        rows = [
            # fully empty rows are dropped by the reader, so the number is an estimate of the Excel row
            (index + 2, {field: row.get(key) for key, field in mapping.items()})
            for index, row in enumerate(records)
            if index > header_index
        ]
        return ZSheet(sheet=sheet, period=period, rows=rows)

    def build(self) -> list[ZSheet]:
        try:
            names = ExcelReader().sheet_names(self.file)
        except Exception as exc:
            raise ImportFileError(MSG_FILE.format(name=self.file.filename)) from exc
        sheets = []
        for name in names:
            period = self.period_of(name)
            if period is None:
                continue
            if not period:
                sheets.append(ZSheet(sheet=name, period="", problem=f"Không đọc được tháng từ tên sheet '{name}'."))
                continue
            sheets.append(self._sheet(name, period))
        if not sheets:
            raise ImportFileError(MSG_NO_SHEET)
        return sheets

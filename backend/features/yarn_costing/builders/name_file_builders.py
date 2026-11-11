"""Tên sợi (bổ sung 2026-11-11): 5.13 file sửa tên hàng loạt (ra / vào) và file đề xuất giữ / loại tên trùng (UC-71)."""

from typing import Any

from backend.core.base import BaseBuilder, FileDownloadDTO, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.yarn_costing.builders.file_builders import xlsx
from backend.features.yarn_costing.constants import MAX_SHEET_ROWS
from backend.features.yarn_costing.dto.name_dto import DuplicateDecisionDTO, SuspectNameDTO
from backend.features.yarn_costing.exceptions import ImportFileError
from backend.shared.file_io.excel import ExcelReader
from backend.shared.utils.text import normalize_key

RENAME_SHEET = "Sua ten"
COLUMNS = {"factory": "Xưởng", "code": "Mã", "new_name": "Tên mới", "reason": "Lý do sửa"}
MSG_FILE = "Không đọc được file '{name}'. Hãy kiểm tra lại file Excel."
MSG_TOO_BIG = "File phải là .xlsx, .xlsm hoặc .xls, không quá 60 MB và mỗi sheet không quá 10.000 dòng."
MSG_NO_SHEET = "File không có sheet 'Sua ten'."
MSG_MISSING = "File thiếu cột bắt buộc: {columns}."


class RenameListFileBuilder(BaseBuilder[FileDownloadDTO]):
    """5.13 out: suspect names with empty 'Tên mới' / 'Lý do sửa' columns."""

    def __init__(self, rows: list[SuspectNameDTO], filename: str) -> None:
        self.rows, self.filename = rows, filename

    def build(self) -> FileDownloadDTO:
        data = [
            {
                "Xưởng": r.factory_code.value,
                "Mã": r.yarn_code,
                "Trạng thái": r.status.value,
                "Tên hiện tại": r.yarn_name,
                "Lý do nghi sai": ", ".join(i.value for i in r.issues) + (f" - {r.detail}" if r.detail else ""),
                "Gợi ý": r.suggested_name,
                "Tên mới": "",
                "Lý do sửa": "",
            }
            for r in self.rows
        ]
        return xlsx(self.filename, {RENAME_SHEET: data})


class RenameFileReaderBuilder(BaseBuilder[list[tuple[int, dict[str, Any]]]]):
    """5.13 in: rows (excel row, {factory, code, new_name, reason}); rows without 'Tên mới' are skipped."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> list[tuple[int, dict[str, Any]]]:
        try:
            names = ExcelReader().sheet_names(self.file)
        except Exception as exc:
            raise ImportFileError(MSG_FILE.format(name=self.file.filename)) from exc
        sheet = next((n for n in names if normalize_key(n) == normalize_key(RENAME_SHEET)), None)
        if sheet is None:
            raise ImportFileError(MSG_NO_SHEET)
        try:
            records = ExcelReader(sheet_name=sheet, max_rows=MAX_SHEET_ROWS).read(self.file)
        except FileProcessingError as exc:
            raise ImportFileError(
                MSG_TOO_BIG if "rows" in str(exc) else MSG_FILE.format(name=self.file.filename)
            ) from exc
        headers = {normalize_key(k): k for k in (records[0] if records else {})}
        mapping = {field: headers.get(normalize_key(label)) for field, label in COLUMNS.items()}
        missing = [COLUMNS[f] for f, key in mapping.items() if key is None]
        if missing:
            raise ImportFileError(MSG_MISSING.format(columns=", ".join(missing)))
        rows = []
        for index, record in enumerate(records):
            cells = {field: record.get(key) for field, key in mapping.items()}  # type: ignore[arg-type]
            if str(cells.get("new_name") or "").strip():
                rows.append((index + 2, cells))
        return rows


class DuplicatePlanFileBuilder(BaseBuilder[FileDownloadDTO]):
    """UC-71 'Tải đề xuất (Excel)'."""

    def __init__(self, decisions: list[DuplicateDecisionDTO], filename: str) -> None:
        self.decisions, self.filename = decisions, filename

    def build(self) -> FileDownloadDTO:
        data = [
            {
                "Xưởng": d.factory_code.value,
                "Tên sau khi viết hoa": d.upper_name,
                "Đề xuất": "GIỮ" if d.keep else "LOẠI",
                "Mã": d.yarn_code,
                "Tên hiện tại": d.yarn_name,
                "Trạng thái": d.status.value,
                "Mã kế toán": ", ".join(d.accounting_codes),
                "Mã giữ": d.keep_code,
                "Lý do": d.reason,
            }
            for d in self.decisions
        ]
        return xlsx(self.filename, {"De xuat giu - loai": data})

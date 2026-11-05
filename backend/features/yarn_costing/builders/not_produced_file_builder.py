"""5.8 File đánh dấu không sản xuất (UC-48, bổ sung 2026-11-05): read the uploaded file, build the template."""

from backend.core.base import BaseBuilder, FileDownloadDTO, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.yarn_costing.builders.file_builders import xlsx
from backend.features.yarn_costing.constants import MAX_SHEET_ROWS
from backend.features.yarn_costing.exceptions import ImportFileError
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.shared.file_io.excel import ExcelReader
from backend.shared.utils.text import normalize_key

NP_SHEET = "Khong san xuat"
COL_CODE = "Mã"
COL_REASON = "Lý do"
MSG_MISSING = "Sheet '{sheet}' thiếu cột bắt buộc: {columns}."
GUIDE = [
    {
        "Hướng dẫn": "Mỗi dòng một mã cần đánh dấu Không sản xuất. Cột 'Mã' và 'Lý do' bắt buộc; các cột khác được bỏ qua."
    },
    {"Hướng dẫn": "Mã gốc hoặc mã ĐCNSM đều được: app đánh dấu mã gốc cùng mọi bản ĐCNSM của nó."},
    {"Hướng dẫn": "Không đánh dấu được: mã 'Chờ xưởng xem' (dùng Từ chối), mã có mã kế toán, mã đã huỷ / từ chối."},
    {"Hướng dẫn": "Khi lưu: các dòng giá của mã bị gỡ khỏi bảng giá (số cũ còn trong Lịch sử giá)."},
]


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


class NotProducedFileReaderBuilder(BaseBuilder[list[tuple[int, str, str]]]):
    """First sheet, header in row 1, columns 'Mã' and 'Lý do' found by name → (excel row, code, reason)."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> list[tuple[int, str, str]]:
        reader = ExcelReader(sheet_name=0, max_rows=MAX_SHEET_ROWS)
        try:
            records = reader.read(self.file)
        except FileProcessingError as exc:
            raise ImportFileError(
                "File phải là .xlsx, .xlsm hoặc .xls, không quá 60 MB và mỗi sheet không quá 10.000 dòng."
                if "rows" in str(exc)
                else f"Không đọc được file '{self.file.filename}'. Hãy kiểm tra lại file Excel."
            ) from exc
        except Exception as exc:
            raise ImportFileError(f"Không đọc được file '{self.file.filename}'. Hãy kiểm tra lại file Excel.") from exc
        headers = list(records[0].keys()) if records else []
        by_key = {normalize_key(h): h for h in headers}
        code_col, reason_col = by_key.get(normalize_key(COL_CODE)), by_key.get(normalize_key(COL_REASON))
        missing = [name for name, col in ((COL_CODE, code_col), (COL_REASON, reason_col)) if col is None]
        if missing:
            try:
                sheet = reader.sheet_names(self.file)[0]
            except Exception:
                sheet = NP_SHEET
            raise ImportFileError(MSG_MISSING.format(sheet=sheet, columns=", ".join(missing)))
        # header = Excel row 1; fully empty rows are dropped by the reader, so the number is the data position + 1
        return [(index + 2, _text(row.get(code_col)), _text(row.get(reason_col))) for index, row in enumerate(records)]


class NotProducedTemplateBuilder(BaseBuilder[FileDownloadDTO]):
    """5.8 mau-danh-dau-khong-san-xuat-<S1|S4>.xlsx: sheet 'Khong san xuat' (Mã, Lý do) + 'Huong dan'."""

    def __init__(self, factory: FactoryCode) -> None:
        self.factory = factory

    def build(self) -> FileDownloadDTO:
        sample = [
            {COL_CODE: f"{self.factory.value}-0000", COL_REASON: "Excel không có giá - ngành xác nhận không sản xuất"}
        ]
        return xlsx(f"mau-danh-dau-khong-san-xuat-{self.factory.value}.xlsx", {NP_SHEET: sample, "Huong dan": GUIDE})

"""Line Strength file -> raw rows (section 5.1, BR-81, thêm 2026-11-12). Headers are matched without case, accents or
extra spaces. No decisions here: the business decides whether the file is a Line Strength file and what is kept."""

from typing import Any

from backend.core.base import BaseBuilder, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.sewing_productivity.builders.upload_read_builders import cell_text, map_columns
from backend.features.sewing_productivity.constants import (
    MAX_SHEET_ROWS,
    MESSAGE_BR01,
    STRENGTH_GROUP_COLUMNS,
    STRENGTH_HEADER_ROW,
    STRENGTH_OTHER_COLUMNS,
    STRENGTH_RECOGNIZING_COLUMNS,
)
from backend.features.sewing_productivity.exceptions import UploadFileError
from backend.features.sewing_productivity.models.upload_values import RawStrengthFile, RawStrengthRow
from backend.shared.file_io import ExcelReader

EXCEL_ROWS_BEFORE_DATA = 2  # the header is Excel row 1, so data row index 0 is Excel row 2


class LineStrengthReadBuilder(BaseBuilder[RawStrengthFile]):
    """The first sheet of the workbook read as a Line Strength file."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> RawStrengthFile:
        reader = ExcelReader(sheet_name=0, header_row=STRENGTH_HEADER_ROW, max_rows=MAX_SHEET_ROWS)
        try:
            rows = reader.read(self.file)
        except FileProcessingError as exc:
            raise UploadFileError(MESSAGE_BR01) from exc
        headers = [str(header) for header in rows[0]] if rows else []
        mapping = map_columns(headers, {**STRENGTH_RECOGNIZING_COLUMNS, **STRENGTH_OTHER_COLUMNS})
        if any(field not in mapping for field in STRENGTH_RECOGNIZING_COLUMNS):
            return RawStrengthFile()
        missing = tuple(names[0] for field, names in STRENGTH_OTHER_COLUMNS.items() if field not in mapping)
        first_group = headers.index(mapping["groups"])
        group_headers = headers[first_group : first_group + STRENGTH_GROUP_COLUMNS]
        return RawStrengthFile(
            recognized=True,
            missing=missing,
            rows=[self._row(index, raw, mapping, group_headers) for index, raw in enumerate(rows)],
        )

    @staticmethod
    def _row(index: int, raw: dict[str, Any], mapping: dict[str, str], groups: list[str]) -> RawStrengthRow:
        def text(field: str) -> str:
            return cell_text(raw.get(mapping[field])) if field in mapping else ""

        return RawStrengthRow(
            row_number=index + EXCEL_ROWS_BEFORE_DATA,
            factory_code=text("factory"),
            line_text=text("line"),
            groups=[value for header in groups if (value := cell_text(raw.get(header)))],
            buyers=text("buyers"),
            changeover_speed=text("changeover_speed"),
            remark=text("remark"),
        )

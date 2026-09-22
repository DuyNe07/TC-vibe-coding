"""Uploaded Excel file -> list[ImportRow] (header matching by aliases, value normalization, BR-10 format)."""

from typing import Any

from backend.core.base import BaseBuilder, UploadedFileDTO
from backend.features.sample_product_import.constants import (
    ALLOWED_IMPORT_EXTENSIONS,
    IMPORT_COLUMNS,
    MAX_IMPORT_FILE_MB,
)
from backend.features.sample_product_import.exceptions import ImportFileError
from backend.features.sample_product_import.models.import_row import ImportRow
from backend.shared.file_io import ExcelReader
from backend.shared.utils import normalize_key, parse_decimal

HEADER_ROW_NUMBER = 1


class ImportRowsBuilder(BaseBuilder[list[ImportRow]]):
    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> list[ImportRow]:
        self.file.ensure_valid(ALLOWED_IMPORT_EXTENSIONS, MAX_IMPORT_FILE_MB)
        raw_rows = ExcelReader().read(self.file)
        mapping = self._map_headers(list(raw_rows[0].keys()) if raw_rows else [])
        return [self._to_row(index, raw, mapping) for index, raw in enumerate(raw_rows)]

    @staticmethod
    def _map_headers(headers: list[str]) -> dict[str, str]:
        """Return {field: actual header in file}. Raise if a required column is missing."""
        normalized = {normalize_key(h): h for h in headers}
        mapping: dict[str, str] = {}
        for column in IMPORT_COLUMNS:
            for candidate in (normalize_key(column.header), *column.aliases):
                if candidate in normalized:
                    mapping[column.field] = normalized[candidate]
                    break
        missing = [c.header for c in IMPORT_COLUMNS if c.required and c.field not in mapping]
        if missing:
            raise ImportFileError(f"File thiếu cột bắt buộc: {', '.join(missing)}. Hãy dùng file mẫu.")
        return mapping

    @staticmethod
    def _to_row(index: int, raw: dict[str, Any], mapping: dict[str, str]) -> ImportRow:
        def text(field: str) -> str:
            value = raw.get(mapping.get(field, ""))
            return "" if value is None else str(value).strip()

        return ImportRow(
            row_number=index + HEADER_ROW_NUMBER + 1,
            code=text("code").upper(),
            name=text("name"),
            unit=text("unit"),
            quantity=parse_decimal(raw.get(mapping["quantity"])),
            unit_price=parse_decimal(raw.get(mapping["unit_price"])),
        )

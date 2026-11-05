"""Data file -> raw rows. Headers are matched without case, accents or extra spaces (section 5.1). No decisions here."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.core.base import BaseBuilder, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.sewing_productivity.constants import (
    HEADER_INDEX_PRODUCTION,
    HEADER_INDEX_TARGET,
    HEADER_INDEX_WORKER,
    MAX_SHEET_ROWS,
    MESSAGE_BR01,
    PRODUCTION_OPTIONAL_COLUMNS,
    PRODUCTION_REQUIRED_COLUMNS,
    REQUIRED_SHEETS,
    SHEET_PRODUCTION,
    SHEET_TARGET,
    SHEET_WORKER,
    TARGET_OPTIONAL_COLUMNS,
    TARGET_REQUIRED_COLUMNS,
    TEXT_DATE_FORMATS,
    WORKER_COLUMNS,
    WORKER_DATE_COLUMN_INDEX,
    WORKER_DATE_COLUMN_LABEL,
)
from backend.features.sewing_productivity.exceptions import UploadFileError
from backend.features.sewing_productivity.models.upload_values import (
    RawProductionRow,
    RawTargetRow,
    RawWorkbook,
    RawWorkerRow,
    SheetColumns,
)
from backend.shared.file_io import ExcelReader
from backend.shared.utils import normalize_key, parse_decimal

Rows = list[dict[str, Any]]
ColumnSpec = dict[str, tuple[str, ...]]
EXCEL_ROWS_BEFORE_DATA = 2  # a 0-based header index becomes the 1-based Excel row of the first data row


def cell_text(value: object) -> str:
    """Text of a cell. A number stays without a trailing `.0` (Excel gives style 796470 as 796470.0)."""
    if value is None:
        return ""
    if isinstance(value, float | Decimal) and value == value.__trunc__():
        return str(int(value))
    return str(value).strip()


def cell_date(value: object) -> date | None:
    """A date cell: a real date, or text such as `2026/11/03`."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    for text_format in TEXT_DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), text_format).date()
        except ValueError:
            continue
    return None


def map_columns(headers: list[str], spec: ColumnSpec) -> dict[str, str]:
    """{field: header in the file}. The first matching column wins; an exact name goes before a normalized one, so
    `PO#` is not taken for `PO`."""
    exact: dict[str, str] = {}
    normalized: dict[str, str] = {}
    for header in headers:
        exact.setdefault(header.strip().casefold(), header)
        normalized.setdefault(normalize_key(header), header)
    mapping: dict[str, str] = {}
    for field, names in spec.items():
        found = next((exact[name.casefold()] for name in names if name.casefold() in exact), None)
        found = found or next(
            (normalized[normalize_key(name)] for name in names if normalize_key(name) in normalized), None
        )
        if found:
            mapping[field] = found
    return mapping


class WorkbookSheetsBuilder(BaseBuilder[dict[str, str]]):
    """{required sheet name: name in the file}, only for the sheets that were found."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> dict[str, str]:
        try:
            names = ExcelReader().sheet_names(self.file)
        except Exception as exc:  # a file that is not a real workbook fails in several ways inside the library
            raise UploadFileError(MESSAGE_BR01) from exc
        by_key = {normalize_key(name): name for name in names}
        return {sheet: by_key[normalize_key(sheet)] for sheet in REQUIRED_SHEETS if normalize_key(sheet) in by_key}


class RawWorkbookBuilder(BaseBuilder[RawWorkbook]):
    def __init__(self, file: UploadedFileDTO, sheets: dict[str, str]) -> None:
        self.file = file
        self.sheets = sheets

    def build(self) -> RawWorkbook:
        production = self._read(SHEET_PRODUCTION, HEADER_INDEX_PRODUCTION)
        targets = self._read(SHEET_TARGET, HEADER_INDEX_TARGET)
        workers = self._read(SHEET_WORKER, HEADER_INDEX_WORKER)
        production_columns = self._columns(production, {**PRODUCTION_REQUIRED_COLUMNS, **PRODUCTION_OPTIONAL_COLUMNS})
        target_columns = self._columns(targets, {**TARGET_REQUIRED_COLUMNS, **TARGET_OPTIONAL_COLUMNS})
        return RawWorkbook(
            columns=(
                self._missing(SHEET_PRODUCTION, production, production_columns, PRODUCTION_REQUIRED_COLUMNS),
                self._missing(SHEET_TARGET, targets, target_columns, TARGET_REQUIRED_COLUMNS),
                self._missing_worker(workers),
            ),
            production=self._production_rows(production, production_columns),
            targets=self._target_rows(targets, target_columns),
            workers=self._worker_rows(workers),
        )

    def _read(self, sheet: str, header_index: int) -> Rows:
        reader = ExcelReader(sheet_name=self.sheets[sheet], header_row=header_index, max_rows=MAX_SHEET_ROWS)
        try:
            return reader.read(self.file)
        except FileProcessingError as exc:
            raise UploadFileError(MESSAGE_BR01) from exc

    @staticmethod
    def _columns(rows: Rows, spec: ColumnSpec) -> dict[str, str]:
        return map_columns(list(rows[0]), spec) if rows else {}

    @staticmethod
    def _missing(sheet: str, rows: Rows, mapping: dict[str, str], required: ColumnSpec) -> SheetColumns:
        """A sheet without any data row shows no header at all: BR-04 answers for it, not BR-03."""
        if not rows:
            return SheetColumns(sheet=sheet)
        return SheetColumns(
            sheet=sheet, missing=tuple(names[0] for field, names in required.items() if field not in mapping)
        )

    @staticmethod
    def _missing_worker(rows: Rows) -> SheetColumns:
        if not rows:
            return SheetColumns(sheet=SHEET_WORKER)
        headers = list(rows[0])
        mapping = map_columns(headers, {name: (name,) for name in WORKER_COLUMNS})
        missing = [name for name in WORKER_COLUMNS if name not in mapping]
        if len(headers) <= WORKER_DATE_COLUMN_INDEX:
            missing.insert(0, WORKER_DATE_COLUMN_LABEL)
        return SheetColumns(sheet=SHEET_WORKER, missing=tuple(missing))

    @staticmethod
    def _production_rows(rows: Rows, mapping: dict[str, str]) -> list[RawProductionRow]:
        def value(raw: dict[str, Any], field: str) -> object:
            return raw.get(mapping[field]) if field in mapping else None

        return [
            RawProductionRow(
                row_number=index + HEADER_INDEX_PRODUCTION + EXCEL_ROWS_BEFORE_DATA,
                production_date=cell_date(value(raw, "production_date")),
                factory_text=cell_text(value(raw, "factory_text")),
                customer_name=cell_text(value(raw, "customer_name")),
                style=cell_text(value(raw, "style")),
                po_number=cell_text(value(raw, "po_number")),
                source_line=cell_text(value(raw, "source_line")),
                quantity=parse_decimal(value(raw, "quantity")),
                cm_price=parse_decimal(value(raw, "cm_price")),
                sewers=parse_decimal(value(raw, "sewers")),
                working_hours=parse_decimal(value(raw, "working_hours")),
                product_name=cell_text(value(raw, "product_name")) or None,
                color=cell_text(value(raw, "color")) or None,
                smv=parse_decimal(value(raw, "smv")),
                standard_output=parse_decimal(value(raw, "standard_output")),
                match_text=cell_text(value(raw, "match_text")),
            )
            for index, raw in enumerate(rows)
        ]

    @staticmethod
    def _target_rows(rows: Rows, mapping: dict[str, str]) -> list[RawTargetRow]:
        def value(raw: dict[str, Any], field: str) -> object:
            return raw.get(mapping[field]) if field in mapping else None

        return [
            RawTargetRow(
                row_number=index + HEADER_INDEX_TARGET + EXCEL_ROWS_BEFORE_DATA,
                line_text=cell_text(value(raw, "line_text")),
                target_date=cell_date(value(raw, "target_date")),
                daily_target_qty=parse_decimal(value(raw, "daily_target_qty")),
                daily_target_cm=parse_decimal(value(raw, "daily_target_cm")),
                item_name=cell_text(value(raw, "item_name")) or None,
                style=cell_text(value(raw, "style")) or None,
                po_number=cell_text(value(raw, "po_number")) or None,
                expertise=cell_text(value(raw, "expertise")),
            )
            for index, raw in enumerate(rows)
        ]

    @staticmethod
    def _worker_rows(rows: Rows) -> list[RawWorkerRow]:
        """Column C holds the day and has no header; a row without a valid day is not a data row."""
        if not rows or len(rows[0]) <= WORKER_DATE_COLUMN_INDEX:
            return []
        headers = list(rows[0])
        date_header = headers[WORKER_DATE_COLUMN_INDEX]
        mapping = map_columns(headers, {name: (name,) for name in WORKER_COLUMNS})
        result: list[RawWorkerRow] = []
        for raw in rows:
            day = cell_date(raw.get(date_header))
            if day is not None:
                counts = {name: parse_decimal(raw.get(header)) for name, header in mapping.items()}
                result.append(RawWorkerRow(work_date=day, counts=counts))
        return result

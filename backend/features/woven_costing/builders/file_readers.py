"""Uploaded Excel files -> models: F-01..F-04 fabric files, F-06 customers (no business decision here)."""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.core.base import BaseBuilder, UploadedFileDTO
from backend.core.exceptions import FileProcessingError
from backend.features.woven_costing.constants import (
    COL_AFTER,
    COL_BEFORE,
    COL_CUSTOMER,
    COL_CUSTOMER_CODE,
    COL_FABRIC,
    COL_TCFNO,
    COL_TCFNO_INST,
    COL_TEAM,
    COL_TPM,
    COL_YNAME,
    MAX_FILE_MB,
    MAX_FILE_ROWS,
    SPEC_GROUP_FIELDS,
    STD_COLUMNS,
    STD_REQUIRED,
)
from backend.features.woven_costing.exceptions import WovenFileError
from backend.features.woven_costing.models.customer_import import CustomerFileContent, CustomerRecord
from backend.features.woven_costing.models.enums import FabricSource
from backend.features.woven_costing.models.fabric import FabricSpecs
from backend.features.woven_costing.models.fabric_import import FabricFileContent, WeavingRecord, YarnRecord
from backend.shared.file_io import ExcelReader
from backend.shared.utils import normalize_key, parse_decimal

HEADER_EXTRA_ROWS = 3
_LETTER = re.compile(r"[A-Za-z]")


def read_raw_rows(file: UploadedFileDTO, sheet: str | int = 0) -> list[list[Any]]:
    """Every non-empty row of a sheet as a list of cells (header included). Too many rows -> BR-70 message."""
    try:
        records = ExcelReader(sheet_name=sheet, header_row=None, max_rows=MAX_FILE_ROWS + HEADER_EXTRA_ROWS).read(file)  # type: ignore[arg-type]
    except FileProcessingError as exc:
        if "more than" in str(exc):
            raise WovenFileError(f"File quá lớn (tối đa {MAX_FILE_MB} MB, 50.000 dòng).") from exc
        raise WovenFileError(
            f"File {file.filename} không đọc được. Hãy kiểm tra đúng file Excel (.xlsx / .xls)."
        ) from exc
    rows = []
    for record in records:
        width = max((int(k) for k in record), default=-1) + 1
        rows.append([record.get(str(i)) for i in range(width)])
    return rows


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def number(value: Any) -> Decimal | None:
    return parse_decimal(value) if not isinstance(value, str) or value.strip() else None


def to_date(value: Any) -> date | None:
    """yyyy/mm/dd (Peace), dd/mm/yyyy (WFX) or an Excel date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = text(value)
    for pattern in ("%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw[:10], pattern).date()
        except ValueError:
            continue
    return None


def _index(header: list[Any]) -> dict[str, int]:
    index: dict[str, int] = {}
    for i, cell in enumerate(header):
        key = normalize_key(cell)
        if key and key not in index:
            index[key] = i
    return index


class FabricFileReaderBuilder(BaseBuilder[FabricFileContent]):
    """One Peace / WFX file: kind by header (Before -> Weaving control, YNAME -> TCFNO Standard), WFX when the weaving
    file has no TCFNO_INST or the standard file has TPM."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> FabricFileContent:
        rows = read_raw_rows(self.file)
        header = rows[0] if rows else []
        index = _index(header)
        if normalize_key(COL_BEFORE) in index:
            system = FabricSource.PEACE if normalize_key(COL_TCFNO_INST) in index else FabricSource.WFX
            return self._weaving(rows, index, system)
        if normalize_key(COL_YNAME) in index:
            system = FabricSource.WFX if normalize_key(COL_TPM) in index else FabricSource.PEACE
            return self._standard(rows, header, system)
        missing = [c for c in (COL_TCFNO, COL_FABRIC) if normalize_key(c) not in index] or [COL_BEFORE]
        return FabricFileContent(file_name=self.file.filename, system=FabricSource.PEACE, is_weaving=True,
                                 missing_columns=missing)  # fmt: skip

    def _weaving(self, rows: list[list[Any]], index: dict[str, int], system: FabricSource) -> FabricFileContent:
        missing = [c for c in (COL_TCFNO, COL_FABRIC) if normalize_key(c) not in index]
        content = FabricFileContent(
            file_name=self.file.filename, system=system, is_weaving=True, missing_columns=missing
        )
        if missing:
            return content
        before, after = index[normalize_key(COL_BEFORE)], index.get(normalize_key(COL_AFTER))

        def cell(row: list[Any], name: str) -> Any:
            i = index.get(normalize_key(name))
            return row[i] if i is not None and i < len(row) else None

        records = []
        for row in rows[1:]:
            code = text(cell(row, COL_TCFNO))
            if not code or not _LETTER.search(code):
                continue
            values: dict[str, Decimal | None] = {}
            for prefix, start in (("greige_", before), ("finished_", after)):
                if start is None:
                    continue
                for offset, field in enumerate(SPEC_GROUP_FIELDS):
                    if field and start + offset < len(row):
                        values[prefix + field] = number(row[start + offset])
            records.append(
                WeavingRecord(
                    raw_code=code,
                    fabric_name=text(cell(row, COL_FABRIC)),
                    structure=text(cell(row, "Structure")),
                    fabric_kind=text(cell(row, "Fabric Kind")),
                    tcfno_status=text(cell(row, "TCFNO Status")),
                    created_date=to_date(cell(row, "Date create")),
                    in_charge=text(cell(row, "In-Charge")),
                    remark=text(cell(row, "Remark")),
                    specs=FabricSpecs(**{k: v for k, v in values.items() if v is not None and v >= 0}),
                )
            )
        return content.model_copy(update={"weaving_rows": records})

    def _standard(self, rows: list[list[Any]], header: list[Any], system: FabricSource) -> FabricFileContent:
        missing = [name for name, pos in STD_REQUIRED if pos >= len(header) or not text(header[pos])]
        content = FabricFileContent(file_name=self.file.filename, system=system, is_weaving=False,
                                    missing_columns=missing)  # fmt: skip
        if missing:
            return content

        def cell(row: list[Any], name: str) -> Any:
            pos = STD_COLUMNS[name]
            return row[pos] if pos < len(row) else None

        records = []
        for row in rows[1:]:
            code = text(cell(row, "tcfno"))
            if not code:
                continue
            records.append(
                YarnRecord(
                    raw_code=code,
                    direction=text(cell(row, "direction")),
                    full_yarn_name=text(cell(row, "full_yarn_name")),
                    yarn_code=text(cell(row, "yarn_code")),
                    yarn_name=text(cell(row, "yarn_name")),
                    rate=number(cell(row, "rate")) or Decimal(0),
                    yarn_kind=text(cell(row, "yarn_kind")),
                    raw_yarn_code=text(cell(row, "raw_yarn_code")),
                    raw_yarn_name=text(cell(row, "raw_yarn_name")),
                    raw_rate=number(cell(row, "raw_rate")),
                    tpm=text(cell(row, "tpm")),
                )
            )
        return content.model_copy(update={"yarn_rows": records})


class CustomerFileReaderBuilder(BaseBuilder[CustomerFileContent]):
    """F-06: Team, Customer (required), Mã KH (optional); other columns ignored."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> CustomerFileContent:
        rows = read_raw_rows(self.file)
        index = _index(rows[0] if rows else [])
        missing = [c for c in (COL_TEAM, COL_CUSTOMER) if normalize_key(c) not in index]
        if missing:
            return CustomerFileContent(file_name=self.file.filename, missing_columns=missing)
        team_i, name_i = index[normalize_key(COL_TEAM)], index[normalize_key(COL_CUSTOMER)]
        code_i = index.get(normalize_key(COL_CUSTOMER_CODE))
        records = []
        for row in rows[1:]:
            records.append(
                CustomerRecord(
                    team=text(row[team_i]) if team_i < len(row) else "",
                    name=text(row[name_i]) if name_i < len(row) else "",
                    customer_code=text(row[code_i]) if code_i is not None and code_i < len(row) else "",
                )
            )
        return CustomerFileContent(file_name=self.file.filename, rows=records)

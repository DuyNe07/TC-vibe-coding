"""BR-63 checks of the norm workbook (F-05) and the cells changed against the set in force (UC-07, UC-37)."""

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.constants import (
    MAX_CHANGES_SHOWN,
    NORM_KEY_COLUMNS,
    NORM_OPTIONAL_SHEETS,
    NORM_SHEETS,
    NORM_TEXT_COLUMNS,
    REQUIRED_STAGES,
    SPANDEX_SHEET,
    SPANDEX_TYPE_COLUMN,
    TWIST_HOURS_NAME,
    TWIST_PARAM_NAMES,
    TWIST_STAFF_NAME,
    WARP_CHECK_NAMES,
)
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.norm_file import NormChange, NormSheet, NormWorkbook

TWIST_LEVEL_COLUMN = "Độ săn"


class NormFileRule(BaseBusinessRule[Check]):
    """Target text = sheet, other = row number, items[0] = error."""

    code = "BR-63"
    message = "File định mức không đúng mẫu."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Sheet {target.text} dòng {target.other}: {target.items[0] if target.items else 'lỗi'}."


def _is_number(text: str) -> bool:
    try:
        return Decimal(text.replace(",", "")) >= 0
    except InvalidOperation:
        return False


def row_key(sheet: str, row: list[str]) -> str:
    size = NORM_KEY_COLUMNS.get(sheet, 1)
    return " | ".join(cell.strip() for cell in row[:size])


class NormBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (NormFileRule(),)

    def _error(self, sheet: str, row: int, text: str) -> str:
        return NormFileRule().describe_violation(Check(ok=False, text=sheet, other=str(row), items=[text]))

    def validate(self, book: NormWorkbook) -> list[str]:
        """BR-63: 12 sheets (+ optional sheet `Spandex`), columns in order, numbers >= 0, unique keys, keys needed by
        the formulas present; spandex type an integer > 0."""
        errors: list[str] = []
        for name, columns in NORM_SHEETS.items():
            sheet = book.sheet(name)
            if sheet is None:
                if name not in NORM_OPTIONAL_SHEETS:
                    errors.append(self._error(name, 0, "thiếu sheet"))
                continue
            wanted = [c for c in columns if c]
            got = [c.strip() for c in sheet.columns]
            missing = [c for c in wanted if c not in got]
            if missing:
                errors.append(self._error(name, 1, f"thiếu cột {', '.join(missing)}"))
                continue
            errors += self._check_rows(sheet, wanted)
        errors += self._check_required(book)
        return errors

    def _check_rows(self, sheet: NormSheet, columns: list[str]) -> list[str]:
        errors: list[str] = []
        seen: set[str] = set()
        index = {c.strip(): i for i, c in enumerate(sheet.columns)}
        for number, row in enumerate(sheet.rows, start=2):
            cells = {c: (row[index[c]] if index[c] < len(row) else "").strip() for c in columns}
            if sheet.name == "ChiSo" and not cells.get("Chi số"):
                level = cells.get(TWIST_LEVEL_COLUMN, "")
                if level and not _is_number(level):
                    errors.append(self._error(sheet.name, number, f"{TWIST_LEVEL_COLUMN} phải là số ≥ 0"))
                continue
            for column, value in cells.items():
                numeric = column not in NORM_TEXT_COLUMNS and sheet.name != "DanhMuc"
                if numeric and value and not _is_number(value):
                    errors.append(self._error(sheet.name, number, f"cột {column} phải là số ≥ 0"))
            key = row_key(sheet.name, [cells.get(c, "") for c in columns])
            if sheet.name == SPANDEX_SHEET:
                kind = _positive_integer(cells.get(SPANDEX_TYPE_COLUMN, ""))
                if kind is None:
                    errors.append(self._error(sheet.name, number, f"cột {SPANDEX_TYPE_COLUMN} phải là số nguyên > 0"))
                key = str(kind) if kind is not None else key
            if key in seen:
                errors.append(self._error(sheet.name, number, f"khóa {key} bị trùng"))
            seen.add(key)
        return errors

    def _check_required(self, book: NormWorkbook) -> list[str]:
        errors: list[str] = []
        required = {
            "DonGiaPhut": REQUIRED_STAGES,
            "ThamSoSe": (*TWIST_PARAM_NAMES, TWIST_STAFF_NAME, TWIST_HOURS_NAME),
            "ThamSoMacKiem": WARP_CHECK_NAMES,
        }
        for name, keys in required.items():
            sheet = book.sheet(name)
            if sheet is None:
                continue
            present = {(row[0] if row else "").strip().casefold() for row in sheet.rows}
            for key in keys:
                if key.casefold() not in present:
                    errors.append(self._error(name, 0, f"thiếu dòng {key}"))
        return errors

    def changes(self, old: NormWorkbook, new: NormWorkbook) -> list[NormChange]:
        """UC-07 step 2: cells that differ from the set in force (by sheet, key and column), at most 300."""
        changes: list[NormChange] = []
        for new_sheet in new.sheets:
            old_sheet = old.sheet(new_sheet.name)
            old_rows = {row_key(new_sheet.name, r): r for r in (old_sheet.rows if old_sheet else [])}
            for row in new_sheet.rows:
                key = row_key(new_sheet.name, row)
                before = old_rows.get(key)
                for i, column in enumerate(new_sheet.columns):
                    if not column:
                        continue
                    new_value = row[i].strip() if i < len(row) else ""
                    old_value = before[i].strip() if before is not None and i < len(before) else ""
                    if before is None or not _same(old_value, new_value):
                        if before is None and i > 0:
                            continue
                        changes.append(NormChange(sheet=new_sheet.name, key=key, column=column,
                                                  old_value="" if before is None else old_value,
                                                  new_value=new_value))  # fmt: skip
        return changes[:MAX_CHANGES_SHOWN]


SAME_PRECISION = Decimal("1e-12")


def _positive_integer(text: str) -> int | None:
    """BR-63 spandex type: an integer > 0 ("40" or "40.0"); None otherwise."""
    try:
        value = Decimal(text.replace(",", ""))
    except InvalidOperation:
        return None
    return int(value) if value > 0 and value == value.to_integral_value() else None


def _same(left: str, right: str) -> bool:
    """Numbers equal up to the precision Excel keeps (15 significant digits); texts without case."""
    try:
        a, b = Decimal(left or "0"), Decimal(right or "0")
    except InvalidOperation:
        return left.strip().casefold() == right.strip().casefold()
    return abs(a - b) <= max(abs(a), abs(b)) * SAME_PRECISION

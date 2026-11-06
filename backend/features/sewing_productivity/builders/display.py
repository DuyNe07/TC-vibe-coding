"""Rounding and conversions for DTOs and Excel files (BR-50: only here, never in a calculation)."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.models.enums import Assessment, NumberKind

NOT_AVAILABLE = "-"
KIND_DECIMALS = {
    NumberKind.INTEGER: 0,
    NumberKind.PERCENT: 1,
    NumberKind.MONEY: 2,
    NumberKind.KPI: 3,
    NumberKind.PEOPLE: 1,
}


def as_float(value: Decimal | None) -> float | None:
    """A DTO value: exact enough for display; pages round it when they format it."""
    return None if value is None else float(value)


def is_below(assessment: Assessment | None) -> bool:
    """The BR-28 result as a flag for pages."""
    return assessment == Assessment.BELOW


def suffix_of(kind: NumberKind) -> str:
    return "%" if kind == NumberKind.PERCENT else ""


def excel_value(value: Decimal | None, kind: NumberKind) -> float | int | str:
    """A cell of an Excel file: rounded by BR-50, "-" when there is no number (BR-49)."""
    if value is None:
        return NOT_AVAILABLE
    decimals = KIND_DECIMALS[kind]
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    return int(rounded) if decimals == 0 else float(rounded)


def excel_date(day: date | None, label: str = NOT_AVAILABLE) -> str:
    """A date cell of an Excel file; rows without a day show their label."""
    return f"{day:%d/%m/%Y}" if day else label


def with_header(rows: list[dict[str, object]], headers: tuple[str, ...]) -> list[dict[str, object]]:
    """An empty table still writes its header row (the writer reads the header from the first row)."""
    return rows or [dict.fromkeys(headers)]


def file_sheets(sheets: dict[str, list[dict[str, object]]], english: bool) -> dict[str, list[dict[str, object]]]:
    """BR-52: sheet names, column names and text cells of an Excel file in English when asked."""
    if not english:
        return sheets
    return {
        english_name(sheet): [
            {english_name(column): english_name(cell) if isinstance(cell, str) else cell for column, cell in row.items()}
            for row in rows
        ]
        for sheet, rows in sheets.items()
    }

"""BR-81, BR-82, BR-84, BR-86: the Line Strength file (section 4.11) - checking, reading, replacing, and comparing what a
line made with its strong item groups."""

from collections.abc import Iterable
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.core.exceptions import BusinessRuleViolation
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.productivity_business import HUNDRED
from backend.features.sewing_productivity.business.record_sync import rows_to_write
from backend.features.sewing_productivity.constants import (
    MESSAGE_BR81_COLUMNS,
    MESSAGE_BR81_DUPLICATE,
    MESSAGE_BR81_FACTORY,
    SHEET_LINE_STRENGTH,
    STRENGTH_FACTORY_CODES,
    UNCLASSIFIED_GROUP,
)
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.source_records import LineStrength
from backend.features.sewing_productivity.models.stored_record import stable_id
from backend.features.sewing_productivity.models.upload_values import (
    RawStrengthFile,
    RawStrengthRow,
    SkippedRow,
    StrengthUpload,
)


class LineStrengthBusiness(BaseBusiness[RawStrengthRow]):
    def __init__(self) -> None:
        self.cleaning = CleaningBusiness()

    @staticmethod
    def is_strength_file(found_data_sheets: set[str], raw: RawStrengthFile) -> bool:
        """UC-33 a workbook without any sheet of the data file whose first sheet has FAC, LINE, STRONG ITEM GROUP."""
        return not found_data_sheets and raw.recognized

    def read(self, raw: RawStrengthFile, file_name: str) -> StrengthUpload:
        """BR-81 every column there, then the lines kept and the rows skipped."""
        self.ensure_columns(raw)
        lines, skipped = self.parse(raw, file_name)
        return StrengthUpload(lines=lines, skipped=skipped)

    @staticmethod
    def ensure_columns(raw: RawStrengthFile) -> None:
        """BR-81 a recognised Line Strength file has every column of section 5.1."""
        if raw.missing:
            raise BusinessRuleViolation(message=MESSAGE_BR81_COLUMNS.format(columns=", ".join(raw.missing)))

    def parse(self, raw: RawStrengthFile, file_name: str) -> tuple[list[LineStrength], list[SkippedRow]]:
        """BR-81 the lines kept, and the rows skipped with their reason. Rows without FAC and LINE are left out."""
        kept: dict[tuple[Factory, str], LineStrength] = {}
        skipped: list[SkippedRow] = []
        for row in raw.rows:
            if not row.factory_code and not row.line_text:
                continue
            factory = STRENGTH_FACTORY_CODES.get(row.factory_code.strip().upper())
            if factory is None:
                reason = MESSAGE_BR81_FACTORY.format(row=row.row_number, code=row.factory_code)
                skipped.append(SkippedRow(sheet=SHEET_LINE_STRENGTH, row_number=row.row_number, reason=reason))
                continue
            line = self.cleaning.standard_line(row.line_text)
            key = (Factory(factory), line)
            if key in kept:
                reason = MESSAGE_BR81_DUPLICATE.format(row=row.row_number)
                skipped.append(SkippedRow(sheet=SHEET_LINE_STRENGTH, row_number=row.row_number, reason=reason))
                continue
            kept[key] = LineStrength(
                id=stable_id(factory, line),
                factory=Factory(factory),
                line=line,
                strong_groups=[" ".join(group.split()) for group in row.groups],
                buyers=" ".join(row.buyers.split()),
                changeover_speed=row.changeover_speed.strip(),
                remark=row.remark.strip(),
                file_name=file_name,
            )
        return list(kept.values()), skipped

    @staticmethod
    def replacement_writes(
        stored: list[LineStrength], deleted: list[LineStrength], incoming: list[LineStrength], deleted_by: str | None
    ) -> list[LineStrength]:
        """BR-82 the new file replaces every line: changed lines are written, lines left out are flagged deleted."""
        return rows_to_write(stored, deleted, incoming, lambda _row: True, deleted_by)

    @staticmethod
    def strong_map(strengths: Iterable[LineStrength]) -> dict[tuple[Factory, str], frozenset[str]]:
        """BR-86 the strong item groups of each (factory, line), case folded; lines without any group left out."""
        return {
            (item.factory, item.line): frozenset(group.casefold() for group in item.strong_groups)
            for item in strengths
            if item.strong_groups
        }

    @staticmethod
    def row_matches(row: CleanRow, strong: dict[tuple[Factory, str], frozenset[str]]) -> bool | None:
        """BR-86 True when the product group of the row is a strong group of its line; None (not counted) when the
        product is not classified or the line has no strength saved."""
        groups = strong.get((row.factory, row.line))
        if not groups or row.product_group.casefold() == UNCLASSIFIED_GROUP.casefold():
            return None
        return row.product_group.casefold() in groups

    def matching_ratio(
        self, rows: Iterable[CleanRow], strong: dict[tuple[Factory, str], frozenset[str]]
    ) -> Decimal | None:
        """BR-86 output of the matching rows / output of the rows counted (%); None when no row is counted."""
        counted = Decimal(0)
        matched = Decimal(0)
        for row in rows:
            found = self.row_matches(row, strong)
            if found is None:
                continue
            counted += row.quantity
            if found:
                matched += row.quantity
        return matched * HUNDRED / counted if counted else None

    @staticmethod
    def matches(groups: Iterable[str], strength: LineStrength | None) -> bool | None:
        """BR-84 Yes when every product group of the order is a strong group of the line (case ignored); None ("-")
        when the line has no strength saved or a product is not classified."""
        wanted = {group.casefold() for group in groups}
        if strength is None or not strength.strong_groups or not wanted or UNCLASSIFIED_GROUP.casefold() in wanted:
            return None
        return wanted <= {group.casefold() for group in strength.strong_groups}

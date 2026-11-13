"""Checking the data file and turning its rows into stored records (BR-01 to BR-07, BR-16)."""

from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import TypeVar

from backend.core.base import BaseBusiness
from backend.core.exceptions import BusinessRuleViolation
from backend.features.sewing_productivity.business.cleaning_business import base_po_number
from backend.features.sewing_productivity.business.record_sync import rows_to_write
from backend.features.sewing_productivity.business.upload_rules import (
    TARGET_LINE_PATTERN,
    FormulaResultsRule,
    KnownFactoryRule,
    ProductionRowRule,
    RequiredColumnsRule,
    RequiredSheetsRule,
    TargetRowRule,
    UploadFileRule,
)
from backend.features.sewing_productivity.constants import (
    FACTORY_BY_SOURCE_NAME,
    LINE_LABEL_FORMAT,
    MISMATCHED_PRODUCTION_VALUE,
    MISMATCHED_TARGET_VALUE,
    PRODUCTION_ONLY_BEFORE,
    REQUIRED_SHEETS,
    SHEET_PRODUCTION,
    SHEET_TARGET,
    SHEET_WORKER,
    WORKER_COLUMNS,
    WORKER_TOTAL_COLUMNS,
)
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.source_records import ProductionRecord, TargetRecord, WorkerRecord
from backend.features.sewing_productivity.models.stored_record import StoredRecord, stable_id
from backend.features.sewing_productivity.models.upload_values import (
    DateRange,
    ParsedUpload,
    ProductionResultFacts,
    RawProductionRow,
    RawTargetRow,
    RawWorkbook,
    SheetNames,
    SkippedRow,
    UploadFileFacts,
)
from backend.shared.utils import normalize_key

TRecord = TypeVar("TRecord", bound=StoredRecord)


class UploadBusiness(BaseBusiness[RawProductionRow]):
    def rules(self) -> tuple[ProductionRowRule, KnownFactoryRule]:
        return (ProductionRowRule(), KnownFactoryRule())

    def ensure_file(self, facts: UploadFileFacts) -> None:
        """BR-01 format and size. The row limit is enforced when the sheets are read."""
        UploadFileRule().check(facts)

    def ensure_sheets(self, found: set[str]) -> bool:
        """BR-02 the 3 sheets are present (`found` holds the required names that were recognised). Returns True for a
        file with only Production data (BR-97, sửa 2026-11-13): `parse` then checks that it is a past year."""
        missing = tuple(sheet for sheet in REQUIRED_SHEETS if sheet not in found)
        if found == {SHEET_PRODUCTION}:
            return True
        RequiredSheetsRule().check(SheetNames(missing=missing))
        return False

    def parse(self, workbook: RawWorkbook, production_only: bool = False) -> ParsedUpload:
        """BR-03, BR-04, BR-05, BR-06, BR-16: raises when the file is refused, lists the rows it skips. BR-97: with
        `production_only`, every day must be before 2026 and the sewers of each factory and day come from its lines."""
        violations = [v for sheet in workbook.columns if (v := RequiredColumnsRule().evaluate(sheet)) is not None]
        if violations:
            raise BusinessRuleViolation(violations)
        non_blank = [row for row in workbook.production if not row.is_blank]
        production, production_skipped = self._production_records(non_blank)
        cells = sum(1 for record in production if record.standard_output is not None)
        FormulaResultsRule().check(ProductionResultFacts(valid_rows=len(production), standard_output_cells=cells))
        if production_only:
            self._ensure_past_year(production)
        targets, target_skipped = self._target_records(workbook.targets)
        workers = self.derived_workers(production) if production_only else self._worker_records(workbook)
        worker_days = (
            [record.production_date for record in production]
            if production_only
            else [row.work_date for row in workbook.workers]
        )
        return ParsedUpload(
            production=production,
            targets=targets,
            workers=workers,
            skipped=[*production_skipped, *target_skipped],
            production_read=len(non_blank),
            production_skipped=len(production_skipped),
            production_range=self._range([record.production_date for record in production]),
            target_range=self._range([record.target_date for record in targets]),
            worker_range=self._range(worker_days),
            derived_workers=production_only,
        )

    @staticmethod
    def _ensure_past_year(production: list[ProductionRecord]) -> None:
        """BR-97 a file with only Production data is accepted for days before 2026 only; otherwise BR-02 as before."""
        if any(record.production_date >= PRODUCTION_ONLY_BEFORE for record in production):
            RequiredSheetsRule().check(SheetNames(missing=(SHEET_TARGET, SHEET_WORKER)))

    @staticmethod
    def derived_workers(production: list[ProductionRecord]) -> list[WorkerRecord]:
        """BR-97 sewers of a factory on a day = sum over its lines of the line's people that day (BR-21: the average
        of the line's rows)."""
        people: dict[tuple[date, Factory, str], list[Decimal]] = defaultdict(list)
        for record in production:
            people[(record.production_date, record.factory, normalize_key(record.source_line))].append(record.sewers)
        totals: defaultdict[tuple[date, Factory], Decimal] = defaultdict(Decimal)
        for (day, factory, _line), values in people.items():
            totals[(day, factory)] += sum(values, Decimal(0)) / len(values)
        return [
            WorkerRecord(
                id=stable_id(day, factory.value),
                work_date=day,
                factory=factory,
                direct_sewers=count,
                derived=True,
            )
            for (day, factory), count in sorted(totals.items())
            if count > 0
        ]

    def _production_records(self, rows: list[RawProductionRow]) -> tuple[list[ProductionRecord], list[SkippedRow]]:
        records: list[ProductionRecord] = []
        skipped: list[SkippedRow] = []
        occurrences: Counter[tuple[object, ...]] = Counter()
        for row in rows:
            violations = self.collect_violations(row)
            if violations:
                reason = " ".join(violation.message for violation in violations)
                skipped.append(SkippedRow(sheet=SHEET_PRODUCTION, row_number=row.row_number, reason=reason))
                continue
            records.append(self._production_record(row, occurrences))
        return records, skipped

    @staticmethod
    def _production_record(row: RawProductionRow, occurrences: Counter[tuple[object, ...]]) -> ProductionRecord:
        """Section 4.1: the id comes from the identifying columns and the occurrence of that combination."""
        factory = FACTORY_BY_SOURCE_NAME[normalize_key(row.factory_text)]
        identity = (row.production_date, factory.value, row.source_line, row.po_number, row.style, row.color)
        occurrences[identity] += 1
        smv = row.smv if row.smv is not None and row.smv > 0 else None
        standard = row.standard_output if row.standard_output is not None and row.standard_output >= 0 else None
        no_ratio = row.standard_output_no_ratio
        return ProductionRecord(
            id=stable_id(*identity, occurrences[identity]),
            production_date=row.production_date,
            factory=factory,
            customer_name=row.customer_name,
            style=row.style,
            po_number=row.po_number,
            product_name=row.product_name or None,
            color=row.color or None,
            source_line=row.source_line,
            quantity=row.quantity,
            cm_price=row.cm_price,
            working_hours=row.working_hours,
            sewers=row.sewers,
            smv=smv,
            standard_output=standard,
            standard_output_no_ratio=no_ratio if no_ratio is not None and no_ratio >= 0 else None,
            is_mismatched=normalize_key(row.match_text) == MISMATCHED_PRODUCTION_VALUE,
        )

    def _target_records(self, rows: list[RawTargetRow]) -> tuple[list[TargetRecord], list[SkippedRow]]:
        rule = TargetRowRule()
        records: list[TargetRecord] = []
        skipped: list[SkippedRow] = []
        occurrences: Counter[tuple[object, ...]] = Counter()
        for row in rows:
            if row.is_blank:
                continue
            violation = rule.evaluate(row)
            if violation is not None:
                skipped.append(SkippedRow(sheet=SHEET_TARGET, row_number=row.row_number, reason=violation.message))
                continue
            records.append(self._target_record(row, occurrences))
        return records, skipped

    @staticmethod
    def _target_record(row: RawTargetRow, occurrences: Counter[tuple[object, ...]]) -> TargetRecord:
        """BR-16: `<xưởng> - Sewing Line <số>` gives the factory and the line."""
        match = TARGET_LINE_PATTERN.match(row.line_text)
        factory = WORKER_COLUMNS[match.group(1).upper()]
        line = LINE_LABEL_FORMAT.format(int(match.group(2)))
        base_po = base_po_number(row.po_number) if row.po_number else None
        identity = (row.target_date, factory.value, line, base_po, row.style)
        occurrences[identity] += 1
        cm = row.daily_target_cm if row.daily_target_cm is not None and row.daily_target_cm >= 0 else None
        return TargetRecord(
            id=stable_id(*identity, occurrences[identity]),
            target_date=row.target_date,
            factory=factory,
            line=line,
            base_po=base_po,
            style=row.style or None,
            item_name=row.item_name or None,
            daily_target_qty=row.daily_target_qty,
            daily_target_cm=cm,
            is_mismatched=normalize_key(row.expertise) == MISMATCHED_TARGET_VALUE,
        )

    @staticmethod
    def _worker_records(workbook: RawWorkbook) -> list[WorkerRecord]:
        """Section 4.3: one number per factory and day; an empty cell means no number yet."""
        total_column = {factory: column for column, factory in WORKER_TOTAL_COLUMNS.items()}
        records: dict[str, WorkerRecord] = {}
        for row in workbook.workers:
            for column, factory in WORKER_COLUMNS.items():
                count = row.counts.get(column)
                record_id = stable_id(row.work_date, factory.value)
                if count is None or count <= 0 or record_id in records:
                    continue
                total = row.totals.get(total_column[factory])
                records[record_id] = WorkerRecord(
                    id=record_id,
                    work_date=row.work_date,
                    factory=factory,
                    direct_sewers=count,
                    total_workers=total if total is not None and total > 0 else None,
                )
        return list(records.values())

    @staticmethod
    def _range(days: list[date]) -> DateRange:
        return DateRange(from_date=min(days), to_date=max(days)) if days else DateRange()

    def replacement_writes(
        self,
        stored: list[TRecord],
        deleted: list[TRecord],
        incoming: list[TRecord],
        date_range: DateRange,
        date_of: Callable[[TRecord], date],
        deleted_by: str | None,
    ) -> list[TRecord]:
        """BR-07: rows that change, and rows of the sheet's date range that left the file (flagged, never removed)."""

        def in_range(row: TRecord) -> bool:
            return self.is_in_range(date_of(row), date_range)

        return rows_to_write(stored, deleted, incoming, in_range, deleted_by)

    def state_after_save(
        self,
        stored: list[TRecord],
        incoming: list[TRecord],
        date_range: DateRange,
        date_of: Callable[[TRecord], date],
    ) -> list[TRecord]:
        """BR-07: what the table will hold once the file is saved (stored rows out of the range + the file's rows)."""
        return [row for row in stored if not self.is_in_range(date_of(row), date_range)] + incoming

    @staticmethod
    def is_in_range(day: date, date_range: DateRange) -> bool:
        if date_range.from_date is None or date_range.to_date is None:
            return False
        return date_range.from_date <= day <= date_range.to_date

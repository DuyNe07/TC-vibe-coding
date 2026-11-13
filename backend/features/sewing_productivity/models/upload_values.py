"""Values of the upload flow: raw rows read from the file and the result of checking them."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseValueObject
from backend.features.sewing_productivity.models.source_records import (
    LineStrength,
    ProductionRecord,
    TargetRecord,
    WorkerRecord,
)


class DateRange(BaseValueObject):
    from_date: date | None = None
    to_date: date | None = None


class UploadFileFacts(BaseValueObject):
    extension: str
    size_mb: float


class SheetNames(BaseValueObject):
    missing: tuple[str, ...] = ()


class SheetColumns(BaseValueObject):
    sheet: str
    missing: tuple[str, ...] = ()


class ProductionResultFacts(BaseValueObject):
    valid_rows: int
    standard_output_cells: int


class RawProductionRow(BaseValueObject):
    row_number: int
    production_date: date | None = None
    factory_text: str = ""
    customer_name: str = ""
    style: str = ""
    po_number: str = ""
    source_line: str = ""
    quantity: Decimal | None = None
    cm_price: Decimal | None = None
    sewers: Decimal | None = None
    working_hours: Decimal | None = None
    product_name: str | None = None
    color: str | None = None
    smv: Decimal | None = None
    standard_output: Decimal | None = None
    standard_output_no_ratio: Decimal | None = None
    match_text: str = ""

    @property
    def is_blank(self) -> bool:
        keys = (self.factory_text, self.customer_name, self.style, self.po_number, self.source_line)
        return self.production_date is None and not any(keys)


class RawTargetRow(BaseValueObject):
    row_number: int
    line_text: str = ""
    target_date: date | None = None
    daily_target_qty: Decimal | None = None
    daily_target_cm: Decimal | None = None
    item_name: str | None = None
    style: str | None = None
    po_number: str | None = None
    expertise: str = ""

    @property
    def is_blank(self) -> bool:
        return not self.line_text and self.target_date is None and self.daily_target_qty is None


class RawWorkerRow(BaseValueObject):
    work_date: date
    counts: dict[str, Decimal | None]
    totals: dict[str, Decimal | None] = {}  # TOTAL block (headcount), absent in older files


class RawWorkbook(BaseValueObject):
    columns: tuple[SheetColumns, ...]
    production: list[RawProductionRow]
    targets: list[RawTargetRow]
    workers: list[RawWorkerRow]


class RawStrengthRow(BaseValueObject):
    """BR-81 one row of the Line Strength file, as read."""

    row_number: int
    factory_code: str = ""
    line_text: str = ""
    groups: list[str] = []
    buyers: str = ""
    changeover_speed: str = ""
    remark: str = ""


class RawStrengthFile(BaseValueObject):
    """BR-81 the first sheet of a workbook read as a Line Strength file. `recognized`: FAC, LINE and STRONG ITEM GROUP
    were found, so the file is a Line Strength file; `missing`: its other required columns that are absent."""

    recognized: bool = False
    missing: tuple[str, ...] = ()
    rows: list[RawStrengthRow] = []


class SkippedRow(BaseValueObject):
    sheet: str
    row_number: int
    reason: str


class UploadWarning(BaseValueObject):
    kind: str
    warning_date: date | None = None
    count: int
    detail: str = ""


class StrengthUpload(BaseValueObject):
    """UC-33 a Line Strength file once read (BR-81): the lines kept and the rows skipped."""

    lines: list[LineStrength]
    skipped: list[SkippedRow]

    @property
    def read_rows(self) -> int:
        return len(self.lines) + len(self.skipped)


class ParsedUpload(BaseValueObject):
    production: list[ProductionRecord]
    targets: list[TargetRecord]
    workers: list[WorkerRecord]
    skipped: list[SkippedRow]
    production_read: int
    production_skipped: int
    production_range: DateRange
    target_range: DateRange
    worker_range: DateRange
    derived_workers: bool = False  # BR-97: a past-year file with only Production data

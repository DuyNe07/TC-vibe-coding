"""Values of the upload flow: raw rows read from the file and the result of checking them."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseValueObject
from backend.features.sewing_productivity.models.source_records import ProductionRecord, TargetRecord, WorkerRecord


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


class RawWorkbook(BaseValueObject):
    columns: tuple[SheetColumns, ...]
    production: list[RawProductionRow]
    targets: list[RawTargetRow]
    workers: list[RawWorkerRow]


class SkippedRow(BaseValueObject):
    sheet: str
    row_number: int
    reason: str


class UploadWarning(BaseValueObject):
    kind: str
    warning_date: date | None = None
    count: int
    detail: str = ""


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

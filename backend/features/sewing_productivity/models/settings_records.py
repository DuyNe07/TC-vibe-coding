"""Rows edited by the data updater (sections 4.4 to 4.10)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, model_validator

from backend.core.base import BaseValueObject
from backend.features.sewing_productivity.models.enums import Factory, UploadStatus
from backend.features.sewing_productivity.models.stored_record import StoredRecord


class FactoryGoal(StoredRecord):
    factory: Factory
    effective_from: date
    efficiency_target: Decimal = Field(gt=0)
    mo8h_target: Decimal = Field(gt=0)
    efficiency_threshold: Decimal = Field(gt=0)
    mo8h_threshold: Decimal = Field(gt=0)
    updated_by: str = Field(min_length=1)


class WeeklyChangeover(StoredRecord):
    factory: Factory
    from_date: date
    to_date: date
    changeover_count: int = Field(ge=0)
    updated_by: str = Field(min_length=1)

    @model_validator(mode="after")
    def _dates_in_order(self) -> "WeeklyChangeover":
        if self.from_date > self.to_date:
            raise ValueError("from_date must not be after to_date")
        return self


class ProductGroupRule(StoredRecord):
    product_name: str = Field(min_length=1)
    product_group: str = Field(min_length=1)


class CustomerGroupRule(StoredRecord):
    customer_name: str = Field(min_length=1)
    customer_group: str = Field(min_length=1)


class LineMappingRule(StoredRecord):
    old_line: str = Field(min_length=1)
    new_line: str = Field(min_length=1)


class StyleProductRule(StoredRecord):
    style: str = Field(min_length=1)
    product_name: str = Field(min_length=1)


class UploadSheetCount(BaseValueObject):
    """BR-72 one sheet of one upload."""

    sheet: str
    read_rows: int = Field(ge=0)
    valid_rows: int = Field(ge=0)
    skipped_rows: int = Field(ge=0)


class UploadChangeCount(BaseValueObject):
    """BR-73 what one upload did to one sheet of one factory."""

    sheet: str
    factory: Factory
    added: int = Field(default=0, ge=0)
    updated: int = Field(default=0, ge=0)
    hidden: int = Field(default=0, ge=0)


class UploadSkippedNote(BaseValueObject):
    """BR-72 one skipped row, as listed after the save."""

    sheet: str
    row_number: int
    reason: str


class UploadWarningNote(BaseValueObject):
    """BR-72 one BR-08 warning, as listed after the save."""

    kind: str
    warning_date: date | None = None
    count: int
    detail: str = ""


class UploadLog(StoredRecord):
    """Section 4.10. The fields added on 2026-11-09 have defaults: rows saved before read as "Saved, no details"."""

    uploaded_at: datetime
    uploaded_by: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    from_date: date | None = None  # empty only on a rejected upload (sửa 2026-11-09)
    to_date: date | None = None
    saved_rows: int = Field(ge=0)
    skipped_rows: int = Field(ge=0)
    status: UploadStatus = UploadStatus.SAVED  # BR-74
    reject_reason: str = ""
    has_details: bool = False
    sheet_counts: list[UploadSheetCount] = []  # BR-72
    changes: list[UploadChangeCount] = []  # BR-73
    skipped: list[UploadSkippedNote] = []  # BR-72, the first SKIPPED_ROWS_KEPT
    warnings: list[UploadWarningNote] = []  # BR-72

"""Rows edited by the data updater (sections 4.4 to 4.10)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, model_validator

from backend.features.sewing_productivity.models.enums import Factory
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


class UploadLog(StoredRecord):
    uploaded_at: datetime
    uploaded_by: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    from_date: date
    to_date: date
    saved_rows: int = Field(ge=0)
    skipped_rows: int = Field(ge=0)

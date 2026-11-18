"""Rows stored from the data file (sections 4.1, 4.2, 4.3). Only values taken from the file are stored."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.stored_record import StoredRecord


class ProductionRecord(StoredRecord):
    production_date: date
    factory: Factory
    customer_name: str = Field(min_length=1)
    style: str = Field(min_length=1)
    po_number: str = Field(min_length=1)
    product_name: str | None = None
    color: str | None = None
    source_line: str = Field(min_length=1)
    quantity: Decimal = Field(ge=0)
    cm_price: Decimal = Field(gt=0)
    working_hours: Decimal = Field(gt=0)
    sewers: Decimal = Field(gt=0)
    smv: Decimal | None = Field(default=None, gt=0)
    standard_output: Decimal | None = Field(default=None, ge=0)
    standard_output_no_ratio: Decimal | None = Field(default=None, ge=0)  # BR-55: rows saved before it have none
    is_mismatched: bool = False


class TargetRecord(StoredRecord):
    target_date: date
    factory: Factory
    line: str = Field(min_length=1)
    base_po: str | None = None
    style: str | None = None
    item_name: str | None = None
    daily_target_qty: Decimal = Field(ge=0)
    daily_target_cm: Decimal | None = Field(default=None, ge=0)
    is_mismatched: bool = False


class LineStrength(StoredRecord):
    """Section 4.11 (thêm 2026-11-12): one line of the Line Strength file. Id = factory + line (BR-82)."""

    factory: Factory
    line: str = Field(min_length=1)
    strong_groups: list[str] = []
    buyers: str = ""
    changeover_speed: str = ""
    remark: str = ""
    file_name: str = Field(min_length=1)


class WorkerRecord(StoredRecord):
    work_date: date
    factory: Factory
    direct_sewers: Decimal = Field(gt=0)
    total_workers: Decimal | None = Field(default=None, gt=0)  # BR-65: rows saved before 2026-11-06 have none
    derived: bool = False  # BR-97 (thêm 2026-11-13): summed from the lines of a file with only Production data

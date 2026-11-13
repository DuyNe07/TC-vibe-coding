"""Values computed when reading: the cleaned view of a production row and the catalogs it needs."""

import re
from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseValueObject
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.settings_records import FactoryGoal, WeeklyChangeover
from backend.features.sewing_productivity.models.source_records import (
    LineStrength,
    ProductionRecord,
    TargetRecord,
    WorkerRecord,
)
from backend.features.sewing_productivity.models.stored_record import stable_id

_LINE_NUMBER = re.compile(r"(\d+)\s*$")


def catalog_key(text: str) -> str:
    """Catalog lookups ignore case and the spaces at both ends."""
    return text.strip().casefold()


def catalog_id(text: str) -> str:
    """Same catalog key, same row: saving a name again replaces its row."""
    return stable_id(catalog_key(text))


def line_sort_key(line: str) -> tuple[int, str]:
    """Sort `LINE 2` before `LINE 10`; a name without a number goes last."""
    found = _LINE_NUMBER.search(line)
    return (int(found.group(1)), line) if found else (10**9, line)


class CatalogSet(BaseValueObject):
    """The 4 catalogs as lookups, keys made with ``catalog_key``."""

    product_groups: dict[str, str] = {}
    customer_groups: dict[str, str] = {}
    line_mappings: dict[str, str] = {}
    style_products: dict[str, str] = {}


class NameLookup(BaseValueObject):
    """BR-13: the product name chosen for each order and style, in the production data and in `Target system`."""

    by_base_po: dict[str, str] = {}
    by_style: dict[str, str] = {}
    target_by_base_po: dict[str, str] = {}
    target_by_style: dict[str, str] = {}


class CleanRow(BaseValueObject):
    production_date: date
    factory: Factory
    customer_name: str
    customer_group: str
    style: str
    po_number: str
    base_po: str
    product_name: str | None = None
    product_group: str
    color: str | None = None
    line: str
    quantity: Decimal
    cm_price: Decimal
    cm_earning: Decimal
    working_hours: Decimal
    sewers: Decimal
    smv: Decimal | None = None
    standard_output: Decimal | None = None
    standard_output_no_ratio: Decimal | None = None
    is_mismatched: bool = False


class ReportSource(BaseValueObject):
    """Everything a report reads, loaded once per service call."""

    production: list[ProductionRecord] = []
    targets: list[TargetRecord] = []
    workers: list[WorkerRecord] = []
    goals: list[FactoryGoal] = []
    weekly_changeovers: list[WeeklyChangeover] = []
    catalogs: CatalogSet = CatalogSet()
    last_upload_at: datetime | None = None
    strengths: list[LineStrength] = []  # 4.11, BR-86 (thêm 2026-11-13)

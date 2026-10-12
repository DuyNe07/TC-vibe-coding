"""4.17 Giá cũ đối chiếu (Legacy price) + 4.18 Lần nhập file (Import batch)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject, utc_now
from backend.features.yarn_costing.models.enums import FactoryCode, ImportMode
from backend.features.yarn_costing.models.yarn import CostBreakdown


class LegacyPrice(BaseEntity):
    import_id: str
    factory_code: FactoryCode
    yarn_code: str
    cost: CostBreakdown
    total: Decimal
    priced_date_text: str = ""


class SheetCount(BaseValueObject):
    sheet: str
    read: int = 0
    created: int = 0
    updated: int = 0
    rejected: int = 0
    skipped_message: str = ""


class ImportBatch(BaseEntity):
    batch_code: str
    factory_code: FactoryCode
    mode: ImportMode
    cutoff_date: date
    file_name: str
    imported_by: str = ""
    imported_at: datetime = Field(default_factory=utc_now)
    sheets: list[SheetCount] = Field(default_factory=list)

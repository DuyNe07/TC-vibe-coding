"""Rows read from the Peace / WFX files (F-01..F-04) and the result of comparing them with the stored fabrics."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.enums import FabricSource, ImportResult
from backend.features.woven_costing.models.fabric import Fabric, FabricSpecs


class WeavingRecord(BaseValueObject):
    """One data row of a Weaving control file (F-01 / F-03), not cleaned yet."""

    raw_code: str
    fabric_name: str = ""
    structure: str = ""
    fabric_kind: str = ""
    tcfno_status: str = ""
    created_date: date | None = None
    in_charge: str = ""
    remark: str = ""
    specs: FabricSpecs = Field(default_factory=FabricSpecs)


class YarnRecord(BaseValueObject):
    """One data row of a TCFNO Standard file (F-02 / F-04), not cleaned yet."""

    raw_code: str
    direction: str = ""
    full_yarn_name: str = ""
    yarn_code: str = ""
    yarn_name: str = ""
    rate: Decimal = Decimal(0)
    yarn_kind: str = ""
    raw_yarn_code: str = ""
    raw_yarn_name: str = ""
    raw_rate: Decimal | None = None
    tpm: str = ""


class FabricFileContent(BaseValueObject):
    """One uploaded file: its system (Peace / WFX), kind (weaving / standard) and rows."""

    file_name: str
    system: FabricSource
    is_weaving: bool
    weaving_rows: list[WeavingRecord] = Field(default_factory=list)
    yarn_rows: list[YarnRecord] = Field(default_factory=list)
    missing_columns: list[str] = Field(default_factory=list)

    @property
    def row_count(self) -> int:
        return len(self.weaving_rows) if self.is_weaving else len(self.yarn_rows)


class FabricImportRow(BaseValueObject):
    """Result line of UC-01 (one code)."""

    tcfno: str
    fabric_name: str = ""
    source: str = ""
    result: ImportResult
    reason: str = ""


class FabricImportOutcome(BaseValueObject):
    """UC-01 / UC-02: fabrics to save (new + changed), detail rows and counts."""

    to_save: list[Fabric] = Field(default_factory=list)
    rows: list[FabricImportRow] = Field(default_factory=list)
    new_count: int = 0
    changed_count: int = 0
    unchanged_count: int = 0
    missing_yarn_count: int = 0
    error_count: int = 0

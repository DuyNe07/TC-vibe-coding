"""F-06 rows of the customer list (UC-12, UC-36)."""

from pydantic import Field

from backend.core.base import BaseValueObject
from backend.features.woven_costing.models.enums import CustomerImportResult


class CustomerRecord(BaseValueObject):
    team: str = ""
    name: str = ""
    customer_code: str = ""


class CustomerFileContent(BaseValueObject):
    file_name: str
    rows: list[CustomerRecord] = Field(default_factory=list)
    missing_columns: list[str] = Field(default_factory=list)


class CustomerImportLine(BaseValueObject):
    name: str
    customer_code: str
    team: str
    result: CustomerImportResult

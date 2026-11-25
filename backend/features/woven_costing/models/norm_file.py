"""F-05 workbook as plain text cells (read from an upload, or rendered from a norm set for the template / view)."""

from pydantic import Field

from backend.core.base import BaseValueObject


class NormSheet(BaseValueObject):
    name: str
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class NormWorkbook(BaseValueObject):
    sheets: list[NormSheet] = Field(default_factory=list)

    def sheet(self, name: str) -> NormSheet | None:
        return next((s for s in self.sheets if s.name == name), None)


class NormChange(BaseValueObject):
    sheet: str
    key: str
    column: str
    old_value: str = ""
    new_value: str = ""

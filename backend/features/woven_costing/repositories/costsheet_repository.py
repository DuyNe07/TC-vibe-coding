"""Persistence of 4.11-4.20 costsheet versions and 4.19 history."""

from backend.core.base import SqlRepository
from backend.features.woven_costing.models.costsheet import Costsheet, CostsheetHistory


class CostsheetRepository(SqlRepository[Costsheet]):
    def versions(self, costsheet_no: str) -> list[Costsheet]:
        return sorted(self.find_by(costsheet_no=costsheet_no), key=lambda c: c.version)

    def latest_versions(self) -> list[Costsheet]:
        latest: dict[str, Costsheet] = {}
        for sheet in self.list_all():
            current = latest.get(sheet.costsheet_no)
            if current is None or sheet.version > current.version:
                latest[sheet.costsheet_no] = sheet
        return list(latest.values())

    def numbers_of_year(self, year: int) -> list[str]:
        return [c.costsheet_no for c in self.list_all() if f"-{year}-" in c.costsheet_no]


class CostsheetHistoryRepository(SqlRepository[CostsheetHistory]):
    def of_costsheet(self, costsheet_no: str) -> list[CostsheetHistory]:
        return sorted(self.find_by(costsheet_no=costsheet_no), key=lambda h: h.created_at)

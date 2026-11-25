"""Persistence of 4.5 norm sets and 4.6 parameter sets (the initial set is created when the table is empty)."""

from datetime import date

from backend.core.base import SqlRepository
from backend.features.woven_costing.models.norm_set import NormSet, initial_norm_set
from backend.features.woven_costing.models.parameter_set import (
    NEW_TABLES_DATE,
    ParameterSet,
    company_rule_set,
    initial_parameter_set,
)


class NormSetRepository(SqlRepository[NormSet]):
    def list_with_seed(self) -> list[NormSet]:
        rows = self.list_all()
        if not rows:
            rows = [self.add(initial_norm_set())]
        return sorted(rows, key=lambda s: s.effective_from, reverse=True)

    def effective_on(self, day: date) -> NormSet | None:
        """BR-62: the set with effective_from <= day, the latest one."""
        return next((s for s in self.list_with_seed() if s.effective_from <= day), None)

    def by_code(self, code: str) -> NormSet | None:
        return next((s for s in self.list_with_seed() if s.norm_set_code == code), None)


class ParameterSetRepository(SqlRepository[ParameterSet]):
    def list_with_seed(self) -> list[ParameterSet]:
        rows = self.list_all()
        if not rows:
            rows = [self.add(initial_parameter_set())]
        elif self._needs_company_rule_set(rows):
            base = max((s for s in rows if s.effective_from < NEW_TABLES_DATE), key=lambda s: s.effective_from)
            rows.append(self.add(company_rule_set(base)))
        return sorted(rows, key=lambda s: s.effective_from, reverse=True)

    @staticmethod
    def _needs_company_rule_set(rows: list[ParameterSet]) -> bool:
        """4.6 (2026-11-25): a database holding sets saved before the tables existed (no 4.6.1 / 4.6.2 tables stored)
        gets once the set effective 25/11/2026 (company discount steps, liquidation prices 0). A fresh install keeps
        only its initial set."""
        has_old = any(s.tables is None and s.effective_from < NEW_TABLES_DATE for s in rows)
        return has_old and all(s.effective_from != NEW_TABLES_DATE for s in rows)

    def effective_on(self, day: date) -> ParameterSet | None:
        """BR-62: the set with effective_from <= day, the latest one."""
        return next((s for s in self.list_with_seed() if s.effective_from <= day), None)

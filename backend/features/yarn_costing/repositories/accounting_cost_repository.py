"""Tables xuan2894__yarn_costing__accounting_cost_month / _line: 4.21, 4.21.1 giá thành kế toán (bổ sung 2026-11-10)."""

from backend.features.yarn_costing.models.accounting_cost import AccountingCostLine, AccountingCostMonth
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class AccountingCostMonthRepository(YarnSqlRepository[AccountingCostMonth]):
    def current(self, period: str) -> AccountingCostMonth | None:
        """BR-81: the one month record in use for a period."""
        return next(iter(self.find_by(period=period)), None)


class AccountingCostLineRepository(YarnSqlRepository[AccountingCostLine]):
    def for_month(self, month_id: str) -> list[AccountingCostLine]:
        return self.find_by(month_id=month_id)

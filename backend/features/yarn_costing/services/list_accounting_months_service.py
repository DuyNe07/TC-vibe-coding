"""UC-53 / UC-54: các tháng giá thành kế toán đã lưu (mới nhất trước). Không lưu gì."""

from backend.core.base import BaseService
from backend.features.yarn_costing.dto.sales_dto import (
    AccountingMonthDTO,
    AccountingMonthListResponse,
    ListAccountingMonthsRequest,
)
from backend.features.yarn_costing.repositories.accounting_cost_repository import AccountingCostMonthRepository


class ListAccountingMonthsService(BaseService[ListAccountingMonthsRequest, AccountingMonthListResponse]):
    def __init__(self, repository: AccountingCostMonthRepository | None = None) -> None:
        self.repository = repository or AccountingCostMonthRepository()

    def execute(self, request: ListAccountingMonthsRequest) -> AccountingMonthListResponse:
        months = sorted(self.repository.list_all(), key=lambda m: m.period, reverse=True)
        return AccountingMonthListResponse(
            items=[
                AccountingMonthDTO(
                    id=m.id,
                    period=m.period,
                    file_name=m.file_name,
                    sheet_name=m.sheet_name,
                    row_count=m.row_count,
                    total_quantity=m.total_quantity,
                    imported_by=m.imported_by,
                    imported_at=m.created_at,
                )
                for m in months
            ]
        )

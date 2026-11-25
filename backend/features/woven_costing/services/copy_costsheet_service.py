"""UC-19 Sao chép costsheet."""

from datetime import date
from uuid import uuid4

from backend.core.base import BaseService, utc_now
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.customer_business import CustomerBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetActionRequest, CostsheetResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.costsheet import CostsheetHistory
from backend.features.woven_costing.models.enums import CostsheetStatus, HistoryAction
from backend.features.woven_costing.repositories.costing_data import load_costing_data, load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class CopyCostsheetService(BaseService[CostsheetActionRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: CostsheetActionRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-19")
        source = self.repository.get(request.costsheet_id)
        if source is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        access.ensure_view(user, source)
        team = access.ensure_team(user)
        customers = CustomerRepository().list_all()
        customer = next((c for c in customers if c.name == source.customer_name), None)
        code = (
            customer.customer_code
            if customer
            else CustomerBusiness().suggest_code(source.customer_name, {c.customer_code for c in customers})
        )
        number = WorkflowBusiness().costsheet_number(
            code, self.today.year, [c.costsheet_no for c in self.repository.list_all()]
        )
        now = utc_now()
        sheet = source.model_copy(
            update={
                "id": uuid4().hex, "costsheet_no": number, "version": 1, "status": CostsheetStatus.NHAP,
                "copied_from": source.label, "sales_username": access.username(user),
                "sales_name": access.display_name(user), "team": team, "costing_date": self.today, "oc_no": "",
                "return_reason": "", "cancel_reason": "", "approved_by": "", "approved_by_name": "",
                "approved_at": None, "created_by": access.username(user), "created_at": now, "updated_at": now,
            }
        )  # fmt: skip
        business = CostsheetBusiness()
        sheet = business.recalculate(sheet, load_costing_data(sheet.tcfno), self.today)
        self.repository.add(sheet)
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=number,
                version=1,
                action=HistoryAction.COPY,
                by=access.username(user),
                by_name=access.display_name(user),
                comment=f"Từ {source.label}",
            )  # fmt: skip
        )
        self.logger.info("UC-19 %s copied to %s", source.label, number)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=f"Đã tạo costsheet {number} từ {source.costsheet_no} v{source.version}.",
        ).build()

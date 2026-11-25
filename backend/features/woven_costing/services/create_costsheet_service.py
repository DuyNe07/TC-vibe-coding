"""UC-15 Tạo costsheet mới."""

from datetime import date

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, CreateCostsheetRequest
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.costsheet import Costsheet, CostsheetHistory
from backend.features.woven_costing.models.enums import HistoryAction
from backend.features.woven_costing.repositories.costing_data import load_costing_data, load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class CreateCostsheetService(BaseService[CreateCostsheetRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: CreateCostsheetRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-15")
        team = access.ensure_team(user)
        customer = next((c for c in CustomerRepository().list_all() if c.name == request.customer_name.strip()), None)
        if customer is None:
            raise WovenCostingError("Vui lòng chọn khách hàng có trong danh sách (hoặc bấm Thêm khách hàng).")
        fabric_biz = FabricBusiness()
        code = fabric_biz.ensure_code(request.tcfno)
        data = load_costing_data(code)
        fabric = fabric_biz.ensure_exists(data.fabric, code)
        workflow = WorkflowBusiness()
        oc_no = workflow.clean_oc(request.oc_no) if request.oc_no.strip() else ""
        if oc_no:
            workflow.ensure_oc(oc_no)
        snapshot = fabric_biz.snapshot(fabric)
        number = workflow.costsheet_number(
            customer.customer_code, self.today.year, [c.costsheet_no for c in self.repository.list_all()]
        )
        sheet = Costsheet(
            costsheet_no=number,
            dye_plant=request.dye_plant,
            customer_name=customer.name,
            market=request.market,
            order_type=request.order_type,
            oc_no=oc_no,
            style=request.style,
            sale_form=request.sale_form,
            greige_buy_price=request.greige_buy_price,
            delivery_date=request.delivery_date,
            sales_username=access.username(user),
            sales_name=access.display_name(user),
            team=team,
            costing_date=request.costing_date or self.today,
            tcfno=code,
            order_meters=request.order_meters,
            price_type=request.price_type,
            fabric_snapshot=snapshot,
            yarn_lines=HintBusiness().build_yarn_lines(snapshot),
            created_by=access.username(user),
        )
        business = CostsheetBusiness()
        sheet = business.recalculate(sheet, data, self.today)
        self.repository.add(sheet)
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=number,
                version=1,
                action=HistoryAction.CREATE,
                by=access.username(user),
                by_name=access.display_name(user),
            )  # fmt: skip
        )
        self.logger.info("UC-15 created %s for %s, fabric %s, %s m", number, customer.name, code, request.order_meters)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=f"Đã tạo costsheet {number} v1.",
        ).build()

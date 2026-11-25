"""UC-17 Lưu nháp (also "Xác nhận giá sợi hôm nay" with confirm_yarn_prices)."""

from datetime import date

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_input_builder import CostsheetInputBuilder
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetInputRequest, CostsheetResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.costsheet import CostsheetHistory
from backend.features.woven_costing.models.enums import CostsheetStatus, HistoryAction
from backend.features.woven_costing.repositories.costing_data import load_costing_data, load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)
from backend.features.woven_costing.repositories.master_repository import CustomerRepository


class SaveDraftService(BaseService[CostsheetInputRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: CostsheetInputRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-17")
        sheet = self.repository.get(request.costsheet_id or "")
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet. Hãy tạo costsheet trước khi lưu nháp.")
        access.ensure_owner(user, sheet)
        workflow = WorkflowBusiness()
        workflow.ensure_editable(sheet)
        fabric = FabricBusiness()
        code = fabric.ensure_code(request.tcfno or sheet.tcfno)
        data = load_costing_data(code)
        typed = request
        if code != sheet.tcfno and data.fabric is not None:
            snapshot = fabric.snapshot(data.fabric)
            sheet = sheet.model_copy(update={"fabric_snapshot": snapshot, "fabric_overridden": False, "tcfno": code,
                                             "yarn_lines": HintBusiness().build_yarn_lines(snapshot)})  # fmt: skip
            typed = request.model_copy(update={"yarn_lines": []})
        sheet = CostsheetInputBuilder(sheet, typed, self.today, request.confirm_yarn_prices).build()
        business = CostsheetBusiness()
        names = [c.name for c in CustomerRepository().list_all()]
        business.check_header(sheet, names, data.fabric is not None)
        oc_no = workflow.clean_oc(request.oc_no) if request.oc_no.strip() else ""
        if oc_no:
            workflow.ensure_oc(oc_no)
        wanted = {o.code: o.used_value for o in request.parameter_overrides}
        sheet = business.recalculate(sheet, data, self.today, wanted)
        update = {"oc_no": oc_no}
        if sheet.status == CostsheetStatus.TRA_LAI:
            workflow.ensure_transition(sheet, CostsheetStatus.NHAP)
            update["status"] = CostsheetStatus.NHAP
        sheet = self.repository.update(sheet.model_copy(update=update))
        comment = "Xác nhận giá sợi hôm nay" if request.confirm_yarn_prices else ""
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=sheet.costsheet_no,
                version=sheet.version,
                action=HistoryAction.SAVE,
                by=access.username(user),
                by_name=access.display_name(user),
                comment=comment,
            )  # fmt: skip
        )
        self.logger.info("UC-17 saved draft %s (confirm prices=%s)", sheet.label, request.confirm_yarn_prices)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=f"Đã lưu nháp costsheet {sheet.costsheet_no} v{sheet.version}.",
        ).build()

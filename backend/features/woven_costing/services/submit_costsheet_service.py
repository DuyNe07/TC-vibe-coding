"""UC-20 Gửi duyệt (saves the typed cells first when they are sent, then checks and sends)."""

from datetime import date

from backend.core.base import BaseService, utc_now
from backend.features.woven_costing.builders.costsheet_input_builder import CostsheetInputBuilder
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.business.submission_business import SubmissionBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetActionRequest, CostsheetResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError, CostsheetValidationError
from backend.features.woven_costing.models.access import SO_TEAM
from backend.features.woven_costing.models.costsheet import CostsheetHistory
from backend.features.woven_costing.models.enums import CostsheetStatus, HistoryAction
from backend.features.woven_costing.models.parameter_set import ParameterValues
from backend.features.woven_costing.repositories.costing_data import load_costing_data, load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)
from backend.features.woven_costing.repositories.master_repository import CustomerRepository
from backend.features.woven_costing.repositories.norm_repository import ParameterSetRepository


class SubmitCostsheetService(BaseService[CostsheetActionRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: CostsheetActionRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-20")
        sheet = self.repository.get(request.costsheet_id)
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        access.ensure_owner(user, sheet)
        workflow = WorkflowBusiness()
        workflow.ensure_editable(sheet)
        business = CostsheetBusiness()
        typed = request.input
        code = FabricBusiness().ensure_code(typed.tcfno if typed and typed.tcfno else sheet.tcfno)
        data = load_costing_data(code)
        wanted = None
        if typed is not None:
            if code != sheet.tcfno and data.fabric is not None:
                snapshot = FabricBusiness().snapshot(data.fabric)
                sheet = sheet.model_copy(update={"fabric_snapshot": snapshot, "fabric_overridden": False, "tcfno": code,
                                                 "yarn_lines": HintBusiness().build_yarn_lines(snapshot)})  # fmt: skip
                typed = typed.model_copy(update={"yarn_lines": []})
            sheet = CostsheetInputBuilder(sheet, typed, self.today, typed.confirm_yarn_prices).build()
            oc_no = workflow.clean_oc(typed.oc_no) if typed.oc_no.strip() else ""
            if oc_no:
                workflow.ensure_oc(oc_no)
            sheet = sheet.model_copy(update={"oc_no": oc_no})
            wanted = {o.code: o.used_value for o in typed.parameter_overrides}
        business.check_header(sheet, [c.name for c in CustomerRepository().list_all()], data.fabric is not None)
        sheet = business.recalculate(sheet, data, self.today, wanted)
        params = ParameterSetRepository().effective_on(sheet.costing_date)
        valid_days = int((params.values if params else ParameterValues()).yarn_price_valid_days)
        holidays = {h.date for h in data.holidays}
        errors = SubmissionBusiness().submit_errors(sheet, self.today, holidays, valid_days)
        if errors:
            self.repository.update(sheet)
            self.logger.info("UC-20 %s blocked: %s", sheet.label, errors)
            raise CostsheetValidationError("Chưa gửi duyệt được:\n" + "\n".join(errors), details=errors)
        versions = self.repository.versions(sheet.costsheet_no)
        auto = workflow.auto_approves(sheet, versions)
        history = CostsheetHistoryRepository()
        who, name = access.username(user), access.display_name(user)
        if auto:
            workflow.ensure_transition(sheet.model_copy(update={"status": CostsheetStatus.CHO_DUYET}),
                                       CostsheetStatus.DA_DUYET)  # fmt: skip
            sheet = sheet.model_copy(update={"status": CostsheetStatus.DA_DUYET, "approved_by": who,
                                             "approved_by_name": f"{name} (duyệt tự động)",
                                             "approved_at": utc_now()})  # fmt: skip
            self.repository.save_many([sheet, *business.superseded(sheet, versions)])
            history.add(CostsheetHistory(costsheet_no=sheet.costsheet_no, version=sheet.version,
                                         action=HistoryAction.AUTO_APPROVE, by=who, by_name=name))  # fmt: skip
            message = f"Phiên bản {sheet.version} không thay đổi giá so với phiên bản đã duyệt nên được duyệt tự động."
        else:
            workflow.ensure_transition(sheet, CostsheetStatus.CHO_DUYET)
            sheet = self.repository.update(sheet.model_copy(update={"status": CostsheetStatus.CHO_DUYET}))
            history.add(CostsheetHistory(costsheet_no=sheet.costsheet_no, version=sheet.version,
                                         action=HistoryAction.SUBMIT, by=who, by_name=name))  # fmt: skip
            approver = "Phòng SO" if sheet.team == SO_TEAM else f"trưởng team {sheet.team}"  # BR-53
            message = (
                f"Đã gửi duyệt costsheet {sheet.costsheet_no} v{sheet.version}. "
                f"Người duyệt: {approver} hoặc trưởng đơn vị."
            )
        self.logger.info("UC-20 %s -> %s (auto=%s)", sheet.label, sheet.status, auto)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=message,
            auto_approved=auto,
        ).build()

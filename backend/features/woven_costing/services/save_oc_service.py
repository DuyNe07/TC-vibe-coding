"""UC-24 Nhập / sửa OC và chốt đơn."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import OC_STATUSES, CostsheetBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, SaveOcRequest
from backend.features.woven_costing.exceptions import CostsheetNotFoundError, WovenCostingError
from backend.features.woven_costing.models.costsheet import CostsheetHistory
from backend.features.woven_costing.models.enums import CostsheetStatus, HistoryAction
from backend.features.woven_costing.repositories.costing_data import load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)


class SaveOcService(BaseService[SaveOcRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None) -> None:
        self.repository = repository or CostsheetRepository()

    def execute(self, request: SaveOcRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-24")
        sheet = self.repository.get(request.costsheet_id)
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        access.ensure_owner(user, sheet)
        if sheet.status not in OC_STATUSES:
            raise WovenCostingError(f"Costsheet đang ở trạng thái {sheet.status.value}, không sửa OC được.")
        workflow = WorkflowBusiness()
        oc_no = workflow.clean_oc(request.oc_no)
        if oc_no:
            workflow.ensure_oc(oc_no)
        closing = request.close_order and sheet.status != CostsheetStatus.DA_CHOT_DON
        if closing:
            workflow.ensure_can_close(sheet, oc_no)
        if closing or sheet.status == CostsheetStatus.DA_CHOT_DON:
            if not oc_no:
                workflow.ensure_can_close(sheet.model_copy(update={"status": CostsheetStatus.DA_DUYET}), oc_no)
            workflow.ensure_oc_free(oc_no, sheet, self.repository.latest_versions())
        update = {"oc_no": oc_no}
        if closing:
            update["status"] = CostsheetStatus.DA_CHOT_DON
        sheet = self.repository.update(sheet.model_copy(update=update))
        action = HistoryAction.CLOSE_ORDER if closing else HistoryAction.EDIT_OC
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=sheet.costsheet_no,
                version=sheet.version,
                action=action,
                by=access.username(user),
                by_name=access.display_name(user),
                comment=oc_no,
            )  # fmt: skip
        )
        self.logger.info("UC-24 %s OC=%s closed=%s", sheet.label, oc_no, closing)
        message = (
            f"Đã chốt đơn costsheet {sheet.costsheet_no} với OC {oc_no}."
            if closing
            else f"Đã lưu OC {oc_no or '(trống)'} cho costsheet {sheet.costsheet_no} v{sheet.version}."
        )
        business = CostsheetBusiness()
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=message,
        ).build()

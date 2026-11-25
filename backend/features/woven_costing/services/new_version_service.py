"""UC-23 Tạo phiên bản mới."""

from datetime import date
from uuid import uuid4

from backend.core.base import BaseService, utc_now
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
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


class NewVersionService(BaseService[CostsheetActionRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: CostsheetActionRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-23")
        source = self.repository.get(request.costsheet_id)
        if source is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        access.ensure_owner(user, source)
        versions = self.repository.versions(source.costsheet_no)
        WorkflowBusiness().ensure_no_open_version(versions)
        latest = max(versions, key=lambda v: v.version)
        now = utc_now()
        sheet = latest.model_copy(
            update={
                "id": uuid4().hex, "version": latest.version + 1, "status": CostsheetStatus.NHAP, "approved_by": "",
                "approved_by_name": "", "approved_at": None, "return_reason": "", "cancel_reason": "",
                "created_at": now, "updated_at": now,
            }
        )  # fmt: skip
        business = CostsheetBusiness()
        sheet = business.recalculate(sheet, load_costing_data(sheet.tcfno), self.today)
        self.repository.add(sheet)
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=sheet.costsheet_no,
                version=sheet.version,
                action=HistoryAction.NEW_VERSION,
                by=access.username(user),
                by_name=access.display_name(user),
            )  # fmt: skip
        )
        self.logger.info("UC-23 %s created from v%s", sheet.label, latest.version)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=f"Đã tạo phiên bản {sheet.version} của costsheet {sheet.costsheet_no}.",
        ).build()

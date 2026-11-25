"""UC-16 Tính / tính lại costsheet (không lưu)."""

from datetime import date

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_input_builder import CostsheetInputBuilder
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetInputRequest, CostsheetResponse
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.costsheet import Costsheet, FabricSnapshot
from backend.features.woven_costing.models.costsheet_result import CostsheetResult, CostWarning
from backend.features.woven_costing.models.costsheet_view import CostsheetView
from backend.features.woven_costing.repositories.costing_data import load_costing_data, load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository

DRAFT_NUMBER = "(chưa lưu)"


class CalculateCostsheetService(BaseService[CostsheetInputRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: CostsheetInputRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        business = CostsheetBusiness()
        if request.costsheet_id:
            sheet = self.repository.get(request.costsheet_id)
            if sheet is None:
                raise CostsheetNotFoundError("Không tìm thấy costsheet.")
            access.ensure_view(user, sheet)
            if not business.is_editable(sheet, user):
                self.logger.info("UC-16 %s is %s: stored results shown (BR-39)", sheet.label, sheet.status)
                view = load_costsheet_view(sheet)
                return CostsheetResponseBuilder(
                    sheet, view, actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source)
                ).build()
        else:
            sheet = Costsheet(
                costsheet_no=DRAFT_NUMBER, costing_date=request.costing_date or self.today, tcfno="",
                fabric_snapshot=FabricSnapshot(tcfno=""), sales_username=access.username(user),
                sales_name=access.display_name(user), team=access.team(user) or "",
            )  # fmt: skip
        code = FabricBusiness().clean_code(request.tcfno or sheet.tcfno)[0]
        data = load_costing_data(code)
        typed = request
        if data.fabric is not None and data.fabric.tcfno != sheet.fabric_snapshot.tcfno:
            snapshot = FabricBusiness().snapshot(data.fabric)
            sheet = sheet.model_copy(update={"fabric_snapshot": snapshot, "fabric_overridden": False, "tcfno": code,
                                             "yarn_lines": HintBusiness().build_yarn_lines(snapshot)})  # fmt: skip
            typed = request.model_copy(update={"yarn_lines": []})
        sheet = CostsheetInputBuilder(sheet, typed, self.today, request.confirm_yarn_prices).build()
        wanted = {o.code: o.used_value for o in request.parameter_overrides}
        if data.fabric is None:
            warning = CostWarning(code="BR-03", blocking=True,
                                  message=f"Mã vải {code or '(trống)'} chưa có trong dữ liệu gốc. Liên hệ SO hoặc PD nhập nhanh mã này.")  # fmt: skip
            sheet = sheet.model_copy(update={"result": CostsheetResult(warnings=[warning])})
        else:
            sheet = business.recalculate(sheet, data, self.today, wanted)
        self.logger.info("UC-16 calculated %s: calculated=%s, %s warnings", sheet.label, sheet.result.calculated,
                         len(sheet.result.warnings))  # fmt: skip
        view = load_costsheet_view(sheet) if request.costsheet_id else CostsheetView(versions=[sheet])
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message="Đã tính lại (chưa lưu).",
            saved=False,
        ).build()

"""UC-14 Sửa thông số vải trên costsheet (mã nhập tay)."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseService
from backend.features.woven_costing.builders.costsheet_response_builder import CostsheetResponseBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetResponse, UpdateFabricOverrideRequest
from backend.features.woven_costing.exceptions import CostsheetNotFoundError
from backend.features.woven_costing.models.costsheet import CostsheetHistory
from backend.features.woven_costing.models.enums import HistoryAction
from backend.features.woven_costing.models.fabric import FabricSpecs, FabricYarn
from backend.features.woven_costing.repositories.costing_data import load_costing_data, load_costsheet_view
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)

HUNDRED = Decimal(100)


class UpdateFabricOverrideService(BaseService[UpdateFabricOverrideRequest, CostsheetResponse]):
    def __init__(self, repository: CostsheetRepository | None = None, today: date | None = None) -> None:
        self.repository = repository or CostsheetRepository()
        self.today = today or date.today()

    def execute(self, request: UpdateFabricOverrideRequest) -> CostsheetResponse:
        access = AccessBusiness()
        user = self.current_user
        access.ensure_use_case(user, "UC-14")
        sheet = self.repository.get(request.costsheet_id)
        if sheet is None:
            raise CostsheetNotFoundError("Không tìm thấy costsheet.")
        access.ensure_owner(user, sheet)
        WorkflowBusiness().ensure_editable(sheet)
        data = load_costing_data(sheet.tcfno)
        fabric = FabricBusiness()
        source = data.fabric.source if data.fabric else sheet.fabric_snapshot.source
        fabric.ensure_override_allowed(sheet.fabric_snapshot, source)
        base = data.fabric.specs if data.fabric else sheet.fabric_snapshot.specs
        typed = {k: v for k, v in request.specs.model_dump().items() if v is not None}
        specs = FabricSpecs(**{**base.model_dump(), **typed})
        changed = [k for k, v in typed.items() if getattr(base, k) != v]
        yarns = list(sheet.fabric_snapshot.yarns)
        if request.yarns:
            yarns = [
                FabricYarn(**{**y.model_dump(), "raw_rate": y.raw_rate or HUNDRED,
                              "raw_yarn_name": y.raw_yarn_name or y.yarn_name})
                for y in request.yarns
                if y.yarn_name.strip()
            ]  # fmt: skip
            fabric.ensure_manual_yarns(yarns)
            HintBusiness().ensure_valid(sum((y.ratio for y in yarns), Decimal(0)))
            if data.fabric is None or yarns != data.fabric.yarns:
                changed.append("yarns")
        snapshot = sheet.fabric_snapshot.model_copy(
            update={"specs": specs, "yarns": yarns, "overridden_fields": changed}
        )
        lines = HintBusiness().build_yarn_lines(snapshot, sheet.yarn_lines)
        sheet = sheet.model_copy(update={"fabric_snapshot": snapshot, "fabric_overridden": True, "yarn_lines": lines})
        business = CostsheetBusiness()
        sheet = self.repository.update(business.recalculate(sheet, data, self.today))
        CostsheetHistoryRepository().add(
            CostsheetHistory(
                costsheet_no=sheet.costsheet_no,
                version=sheet.version,
                action=HistoryAction.SAVE,
                by=access.username(user),
                by_name=access.display_name(user),
                comment="Sửa thông số vải: " + ", ".join(changed),
            )  # fmt: skip
        )
        self.logger.info("UC-14 %s fabric overridden: %s", sheet.label, changed)
        view = load_costsheet_view(sheet)
        return CostsheetResponseBuilder(
            sheet,
            view,
            actions=business.allowed_actions(sheet, user, view.versions, view.fabric_source),
            editable=business.is_editable(sheet, user),
            message=f"Đã cập nhật thông số vải cho costsheet {sheet.costsheet_no}.",
        ).build()

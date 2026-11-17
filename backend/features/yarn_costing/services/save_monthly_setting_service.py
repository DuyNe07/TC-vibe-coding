"""UC-58 Khai báo tháng (đợt 2, BR-88): hồi phế nguyên liệu, phương án pha bông, hệ số norm, F&I mặc định."""

import re

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness, month_text
from backend.features.yarn_costing.dto.material_dto import MaterialSaveResponse, SaveMonthlySettingRequest
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.material_price import (
    COTTON_PLAN_ID,
    COTTON_PLAN_NAME,
    CottonShare,
    GroupRecovery,
    MonthlyMaterialSetting,
)
from backend.features.yarn_costing.repositories.material_price_repository import (
    MaterialPriceGroupRepository,
    MonthlyMaterialSettingRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-58"
PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MSG_PERIOD = "Vui lòng chọn tháng."


class SaveMonthlySettingService(BaseService[SaveMonthlySettingRequest, MaterialSaveResponse]):
    def execute(self, request: SaveMonthlySettingRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        if not PERIOD.match(request.period):
            raise YarnValidationError(MSG_PERIOD)
        names = {g.id: g.name for g in MaterialPriceGroupRepository().list_all()} | {COTTON_PLAN_ID: COTTON_PLAN_NAME}
        plan = [CottonShare(origin=s.origin, percent=s.percent) for s in request.cotton_plan]
        recoveries = [
            GroupRecovery(group_id=r.group_id, usd_per_kg=r.usd_per_kg)
            for r in request.recoveries
            if r.group_id in names
        ]
        MaterialPriceBusiness().ensure_setting_valid(
            request.norm_factor, request.default_fi, plan, recoveries, names, request.coin_usd, request.coin_tax
        )
        supima_group = (
            request.supima_group_id
            if request.supima_group_id in names and request.supima_group_id != COTTON_PLAN_ID
            else ""
        )
        repo = MonthlyMaterialSettingRepository()
        current = repo.for_period(request.period)
        all_settings = repo.list_all()
        previous = MaterialPriceBusiness().latest_before(request.period, all_settings)
        label = access.user_label(self.current_user)
        values = {
            "norm_factor": request.norm_factor,
            "default_fi": request.default_fi,
            "cotton_plan_note": request.cotton_plan_note.strip()[:200],
            "cotton_plan": plan,
            "recoveries": recoveries,
            "updated_by": label,
            "supima_group_id": supima_group,  # BR-113 (bổ sung 2026-11-13)
            "coin_usd": request.coin_usd,
            "coin_tax": request.coin_tax,
        }
        if current is None:
            repo.add(
                MonthlyMaterialSetting(period=request.period, copied_from=previous.period if previous else "", **values)
            )
        else:
            repo.save(current.model_copy(update=values))
        plan_text = " + ".join(f"{s.origin.value} {s.percent * 100:.2f}%" for s in plan) or "-"
        recovery_text = "; ".join(f"{names[r.group_id]} {r.usd_per_kg}" for r in recoveries) or "-"
        AuditLogRepository().add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                f"Khai báo tháng {request.period}",
                f"Hệ số {request.norm_factor}; F&I {request.default_fi}; phương án {plan_text}; hồi phế {recovery_text}",
            )
        )
        return MaterialSaveResponse(message=f"Đã lưu khai báo tháng {month_text(request.period)}.", saved_count=1)

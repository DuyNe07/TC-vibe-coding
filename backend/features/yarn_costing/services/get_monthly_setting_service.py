"""UC-58 (đợt 2): khai báo tháng M - bản đã lưu, hoặc bản nháp chép từ tháng gần nhất trước đó (BR-88)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import group_options
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness
from backend.features.yarn_costing.dto.material_dto import (
    CottonShareDTO,
    GetMonthlySettingRequest,
    MonthlySettingResponse,
    RecoveryDTO,
)
from backend.features.yarn_costing.repositories.material_price_repository import (
    MaterialPriceGroupRepository,
    MonthlyMaterialSettingRepository,
)

USE_CASE = "UC-58"


class GetMonthlySettingService(BaseService[GetMonthlySettingRequest, MonthlySettingResponse]):
    def execute(self, request: GetMonthlySettingRequest) -> MonthlySettingResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        settings = MonthlyMaterialSettingRepository().list_all()
        saved = next((s for s in settings if s.period == request.period), None)
        setting = MaterialPriceBusiness().setting_of(request.period, settings)
        options = group_options(MaterialPriceGroupRepository().list_all())
        names = {o.id: o.name for o in options}
        return MonthlySettingResponse(
            period=request.period,
            saved=saved is not None,
            copied_from=setting.copied_from,
            norm_factor=setting.norm_factor,
            default_fi=setting.default_fi,
            cotton_plan_note=setting.cotton_plan_note,
            cotton_plan=[CottonShareDTO(origin=s.origin, percent=s.percent) for s in setting.cotton_plan],
            recoveries=[
                RecoveryDTO(group_id=r.group_id, group_name=names.get(r.group_id, ""), usd_per_kg=r.usd_per_kg)
                for r in setting.recoveries
                if r.group_id in names
            ],
            group_options=options,
            updated_by=setting.updated_by if saved else "",
            supima_group_id=setting.supima_group_id if setting.supima_group_id in names else "",
            coin_usd=setting.coin_usd,
            coin_tax=setting.coin_tax,
        )

"""UC-55 / UC-57 (đợt 2): nhóm giá nguyên liệu và khai báo mã kho (dữ liệu của thẻ Khai báo)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import group_dto, group_options
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.dto.material_dto import GetMaterialSetupRequest, MaterialSetupResponse, StockItemDTO
from backend.features.yarn_costing.models.enums import MaterialDecision, StockSection
from backend.features.yarn_costing.repositories.material_price_repository import (
    MaterialPriceGroupRepository,
    StockItemSettingRepository,
    StockLineRepository,
    StockMonthRepository,
)

USE_CASE = "UC-57"


class GetMaterialSetupService(BaseService[GetMaterialSetupRequest, MaterialSetupResponse]):
    def execute(self, request: GetMaterialSetupRequest) -> MaterialSetupResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        groups = MaterialPriceGroupRepository().list_all()
        settings = StockItemSettingRepository().list_all()
        months = StockMonthRepository().ordered()
        closing: dict[str, object] = {}
        if months:
            closing = {
                line.accounting_code: line.closing_qty
                for line in StockLineRepository().for_month(months[0].id)
                if line.section == StockSection.NGUYEN_LIEU
            }
        counts: dict[str, int] = {}
        for s in settings:
            if s.decision == MaterialDecision.THEO_NHOM and s.price_group_id:
                counts[s.price_group_id] = counts.get(s.price_group_id, 0) + 1
        items = sorted(
            (
                StockItemDTO(
                    accounting_code=s.accounting_code,
                    item_name=s.item_name,
                    ica_name=s.ica_name,
                    decision=s.decision,
                    price_group_id=s.price_group_id,
                    market=s.market,
                    closing_qty=closing.get(s.accounting_code),  # type: ignore[arg-type]
                    updated_by=s.updated_by,
                )
                for s in settings
            ),
            key=lambda i: (i.decision != MaterialDecision.CHUA_KHAI_BAO, i.ica_name, i.accounting_code),
        )
        return MaterialSetupResponse(
            groups=[group_dto(g, counts.get(g.id, 0)) for g in sorted(groups, key=lambda g: g.name.casefold())],
            group_options=group_options(groups),
            stock_items=items,
            undeclared_count=sum(1 for s in settings if s.decision == MaterialDecision.CHUA_KHAI_BAO),
            latest_period=months[0].period if months else "",
        )

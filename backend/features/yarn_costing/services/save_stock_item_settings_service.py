"""UC-57 Khai báo mã kho nguyên liệu (đợt 2): nhóm giá / Không tính, loại hàng."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.dto.material_dto import MaterialSaveResponse, SaveStockItemSettingsRequest
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import MaterialDecision
from backend.features.yarn_costing.repositories.material_price_repository import (
    MaterialPriceGroupRepository,
    StockItemSettingRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-57"
MSG_NO_GROUP = "Mã {code}: vui lòng chọn nhóm giá."


class SaveStockItemSettingsService(BaseService[SaveStockItemSettingsRequest, MaterialSaveResponse]):
    def execute(self, request: SaveStockItemSettingsRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        repo = StockItemSettingRepository()
        existing = repo.by_code()
        group_ids = {g.id for g in MaterialPriceGroupRepository().list_all()}
        label = access.user_label(self.current_user)
        changed = []
        notes = []
        for row in request.rows:
            current = existing.get(row.accounting_code)
            if current is None:
                continue
            group_id = row.price_group_id if row.decision == MaterialDecision.THEO_NHOM else None
            if row.decision == MaterialDecision.THEO_NHOM and group_id not in group_ids:
                raise YarnValidationError(MSG_NO_GROUP.format(code=row.accounting_code))
            if (current.decision, current.price_group_id, current.market) == (row.decision, group_id, row.market):
                continue
            changed.append(
                current.model_copy(
                    update={
                        "decision": row.decision,
                        "price_group_id": group_id,
                        "market": row.market,
                        "updated_by": label,
                    }
                )
            )
            notes.append(
                f"{row.accounting_code}: {current.decision.value}/{current.market.value} → {row.decision.value}/{row.market.value}"
            )
        repo.save_many(changed)
        if changed:
            AuditLogRepository().add(
                access.audit_entry(self.current_user, USE_CASE, "Mã kho nguyên liệu", "; ".join(notes))
            )
        self.logger.info("Stock item settings saved: %s", len(changed))
        return MaterialSaveResponse(message=f"Đã lưu khai báo {len(changed)} mã kho.", saved_count=len(changed))

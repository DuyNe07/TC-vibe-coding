"""UC-61 Khai báo nhóm cho nhà cung cấp + mô tả (đợt 2, BR-91)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.dto.material_dto import MaterialSaveResponse, SaveArrivalMappingsRequest
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import MaterialDecision
from backend.features.yarn_costing.repositories.material_price_repository import (
    ArrivalMappingRepository,
    MaterialPriceGroupRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-61"
MSG_NO_GROUP = "Cặp {supplier} + {description}: vui lòng chọn nhóm giá."


class SaveArrivalMappingsService(BaseService[SaveArrivalMappingsRequest, MaterialSaveResponse]):
    def execute(self, request: SaveArrivalMappingsRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        repo = ArrivalMappingRepository()
        existing = repo.by_key()
        group_ids = {g.id for g in MaterialPriceGroupRepository().list_all()}
        label = access.user_label(self.current_user)
        changed, notes = [], []
        for row in request.rows:
            current = existing.get((row.supplier_key, row.description_key))
            if current is None:
                continue
            group_id = row.price_group_id if row.decision == MaterialDecision.THEO_NHOM else None
            if row.decision == MaterialDecision.THEO_NHOM and group_id not in group_ids:
                raise YarnValidationError(
                    MSG_NO_GROUP.format(supplier=current.supplier, description=current.description)
                )
            if (current.decision, current.price_group_id) == (row.decision, group_id):
                continue
            changed.append(
                current.model_copy(update={"decision": row.decision, "price_group_id": group_id, "updated_by": label})
            )
            notes.append(f"{current.supplier} + {current.description}: {current.decision.value} → {row.decision.value}")
        repo.save_many(changed)
        if changed:
            AuditLogRepository().add(
                access.audit_entry(self.current_user, USE_CASE, "Nhóm hàng sắp về", "; ".join(notes))
            )
        return MaterialSaveResponse(
            message=f"Đã lưu khai báo nhóm cho {len(changed)} cặp nhà cung cấp + mô tả.", saved_count=len(changed)
        )

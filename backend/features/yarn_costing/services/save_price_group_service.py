"""UC-55 Khai báo nhóm giá nguyên liệu (đợt 2, BR-85): thêm / sửa / xoá (cờ xoá)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness
from backend.features.yarn_costing.dto.material_dto import MaterialSaveResponse, SavePriceGroupRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.enums import MaterialDecision, PriceGroupKind
from backend.features.yarn_costing.models.material_price import MaterialPriceGroup
from backend.features.yarn_costing.repositories.material_price_repository import (
    ArrivalMappingRepository,
    MaterialPriceGroupRepository,
    StockItemSettingRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-55"
MSG_NOT_FOUND = "Không tìm thấy nhóm giá."


class SavePriceGroupService(BaseService[SavePriceGroupRequest, MaterialSaveResponse]):
    def execute(self, request: SavePriceGroupRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        repo = MaterialPriceGroupRepository()
        label = access.user_label(self.current_user)
        audit = AuditLogRepository()
        current = repo.get(request.group_id) if request.group_id else None
        if request.group_id and current is None:
            raise YarnNotFoundError(MSG_NOT_FOUND)
        if request.delete and current is not None:
            freed = 0
            settings = StockItemSettingRepository()
            for setting in settings.find_by(price_group_id=current.id):
                settings.save(
                    setting.model_copy(
                        update={"decision": MaterialDecision.CHUA_KHAI_BAO, "price_group_id": None, "updated_by": label}
                    )
                )
                freed += 1
            mappings = ArrivalMappingRepository()
            for mapping in mappings.find_by(price_group_id=current.id):
                mappings.save(
                    mapping.model_copy(
                        update={"decision": MaterialDecision.CHUA_KHAI_BAO, "price_group_id": None, "updated_by": label}
                    )
                )
            repo.delete(current.id)
            audit.add(access.audit_entry(self.current_user, USE_CASE, current.name, f"Xoá nhóm giá; {freed} mã kho"))
            self.logger.info("Price group %s deleted (%s stock codes freed)", current.name, freed)
            return MaterialSaveResponse(
                message=f"Đã xoá nhóm giá '{current.name}'; {freed} mã kho trở về Chưa khai báo.", saved_count=1
            )
        name = " ".join(request.name.split())
        origin = request.origin if request.kind == PriceGroupKind.COTTON else None
        others = [g for g in repo.list_all() if current is None or g.id != current.id]
        MaterialPriceBusiness().ensure_group_valid(name, request.kind, request.origin, request.note, others)
        if current is None:
            group = repo.add(
                MaterialPriceGroup(
                    name=name,
                    kind=request.kind,
                    origin=origin,
                    note=request.note.strip(),
                    created_by=label,
                    updated_by=label,
                )
            )
            audit.add(
                access.audit_entry(self.current_user, USE_CASE, group.name, f"Thêm nhóm giá ({group.kind.value})")
            )
            return MaterialSaveResponse(message=f"Đã thêm nhóm giá '{group.name}'.", saved_count=1)
        before = f"{current.name} / {current.kind.value} / {current.origin or ''}"
        group = repo.save(
            current.model_copy(
                update={
                    "name": name,
                    "kind": request.kind,
                    "origin": origin,
                    "note": request.note.strip(),
                    "updated_by": label,
                }
            )
        )
        audit.add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                group.name,
                f"{before} → {group.name} / {group.kind.value} / {group.origin or ''}",
            )
        )
        return MaterialSaveResponse(message=f"Đã cập nhật nhóm giá '{group.name}'.", saved_count=1)

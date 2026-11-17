"""UC-61 Sửa lô hàng sắp về (đợt 2, BR-90, BR-91): thêm / sửa / xoá (cờ xoá) trên bảng."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.dto.material_dto import MaterialSaveResponse, SaveArrivalLotsRequest
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.repositories.material_price_repository import (
    ArrivalLotRepository,
    ArrivalMappingRepository,
)
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-61"
MSG_ROW = "Dòng {row}: {problem}"


class SaveArrivalLotsService(BaseService[SaveArrivalLotsRequest, MaterialSaveResponse]):
    def execute(self, request: SaveArrivalLotsRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        business = MaterialStockBusiness()
        repo = ArrivalLotRepository()
        label = access.user_label(self.current_user)
        added, edited = [], []
        for index, row in enumerate(request.rows, start=1):
            cells = row.model_dump()
            cells["factory_code"] = row.factory_code.value if row.factory_code else None
            cells["market"] = row.market.value if row.market else None
            problem = business.check_lot(cells)
            if problem:
                raise YarnValidationError(MSG_ROW.format(row=index, problem=problem))
            current = repo.get(row.id) if row.id else None
            lot = business.lot_from(cells, import_id=current.import_id if current else None)
            if current is None:
                added.append(lot.model_copy(update={"created_by": label, "updated_by": label}))
                continue
            update = {
                field: getattr(lot, field)
                for field in (
                    "supplier",
                    "commodity",
                    "description",
                    "spec",
                    "contract_no",
                    "quantity",
                    "unit_price",
                    "price_currency",
                    "receiving_price",
                    "eta_warehouse",
                    "warehouse",
                    "factory_code",
                    "market",
                    "note",
                )
            }
            if any(getattr(current, k) != v for k, v in update.items()):
                edited.append(current.model_copy(update={**update, "updated_by": label}))
        deleted = [lot_id for lot_id in request.deleted_ids if repo.get(lot_id) is not None]
        repo.save_many([*added, *edited])
        for lot_id in deleted:
            repo.delete(lot_id)
        mappings = ArrivalMappingRepository()
        mappings.save_many(business.new_mappings(added + edited, mappings.by_key()))
        if added or edited or deleted:
            AuditLogRepository().add(
                access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    "Hàng sắp về",
                    f"Thêm {len(added)}, sửa {len(edited)}, xoá {len(deleted)} lô",
                )
            )
        return MaterialSaveResponse(
            message=f"Đã lưu {len(added)} lô thêm, {len(edited)} lô sửa, {len(deleted)} lô xoá.",
            saved_count=len(added) + len(edited) + len(deleted),
        )

"""UC-51 Thêm / sửa / xoá tên theo khách (BR-79; bổ sung 2026-11-10). Xoá = đặt cờ xoá."""

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import customer_name_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.customer_name_business import CustomerNameBusiness
from backend.features.yarn_costing.dto.sales_dto import CustomerNameResponse, SaveCustomerNameRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.models.customer_name import CustomerYarnName
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-51"


class SaveCustomerNameService(BaseService[SaveCustomerNameRequest, CustomerNameResponse]):
    def __init__(self, repository: CustomerYarnNameRepository | None = None) -> None:
        self.repository = repository or CustomerYarnNameRepository()
        self.access = AccessBusiness()
        self.business = CustomerNameBusiness()

    def execute(self, request: SaveCustomerNameRequest) -> CustomerNameResponse:
        self.access.ensure_allowed(self.current_user, USE_CASE)
        base = next((y for y in YarnRepository().list_all() if y.yarn_code == request.base_code), None)
        if base is None:
            raise YarnNotFoundError(f"Không tìm thấy sợi {request.base_code}.")
        label = self.access.user_label(self.current_user)
        audit = AuditLogRepository()
        current = self.repository.get(request.alias_id) if request.alias_id else None
        if request.alias_id and (current is None or current.base_code != base.base_code):
            raise YarnNotFoundError("Không tìm thấy tên theo khách đã chọn.")
        if request.delete and current is not None:
            self.repository.delete(current.id)
            audit.add(
                self.access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    base.base_code,
                    f"- {current.customer_name}: {current.customer_yarn_name}",
                )
            )
            self.logger.info("Customer name %s of %s deleted (flag)", current.id, base.base_code)
            return CustomerNameResponse(
                message=f"Đã xoá tên '{current.customer_yarn_name}' của khách {current.customer_name}."
            )
        if current is not None:
            customer, name, note = self.business.check(
                base,
                current.customer_name,
                request.customer_yarn_name,
                request.note,
                self.repository.list_all(),
                current.id,
            )
            updated = current.model_copy(update={"customer_yarn_name": name, "note": note, "updated_by": label})
            self.repository.update(updated)
            audit.add(
                self.access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    base.base_code,
                    f"{customer}: {current.customer_yarn_name} → {name}" + (f" / ghi chú: {note}" if note else ""),
                )
            )
            self.logger.info("Customer name %s of %s updated", current.id, base.base_code)
            return CustomerNameResponse(message="Đã cập nhật tên theo khách.", item=customer_name_dto(updated))
        customer, name, note = self.business.check(
            base, request.customer_name, request.customer_yarn_name, request.note, self.repository.list_all()
        )
        alias = CustomerYarnName(
            base_code=base.base_code, customer_name=customer, customer_yarn_name=name, note=note, created_by=label
        )
        self.repository.add(alias)
        audit.add(self.access.audit_entry(self.current_user, USE_CASE, base.base_code, f"+ {customer}: {name}"))
        self.logger.info("Customer name of %r added to %s", customer, base.base_code)
        return CustomerNameResponse(
            message=f"Đã thêm tên theo khách cho sợi {base.base_code}.", item=customer_name_dto(alias)
        )

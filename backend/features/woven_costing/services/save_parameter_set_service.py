"""UC-09 Cập nhật bộ tham số chung (2026-11-25: single values + discount table + % B/C table, BR-65, BR-88)."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.parameter_builders import tables_from_dtos
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.dto.common_dto import MessageResponse
from backend.features.woven_costing.dto.master_dto import SaveParameterSetRequest
from backend.features.woven_costing.exceptions import CostsheetValidationError
from backend.features.woven_costing.models.parameter_set import ParameterSet, ParameterValues
from backend.features.woven_costing.models.parameter_tables import ParameterTables
from backend.features.woven_costing.repositories.norm_repository import ParameterSetRepository


class SaveParameterSetService(BaseService[SaveParameterSetRequest, MessageResponse]):
    def __init__(self, repository: ParameterSetRepository | None = None) -> None:
        self.repository = repository or ParameterSetRepository()

    def execute(self, request: SaveParameterSetRequest) -> MessageResponse:
        access = AccessBusiness()
        access.ensure_use_case(self.current_user, "UC-09")
        sets = self.repository.list_with_seed()
        master = MasterBusiness()
        master.ensure_unique_date(request.effective_from, [s.effective_from for s in sets])
        base = sets[0]
        known = set(ParameterValues.model_fields)
        values = base.values.model_copy(update={v.code: v.value for v in request.values if v.code in known})
        old = base.effective_tables()
        typed = tables_from_dtos(request.discount_rows or [], request.bc_rows or [], request.op_rates)
        discount_rows = typed.discount_rows if request.discount_rows is not None else old.discount_rows
        tables = ParameterTables(
            discount_rows=[r.model_copy(update={"interpolate": False}) for r in discount_rows],  # new set: steps
            bc_rows=typed.bc_rows if request.bc_rows is not None else old.bc_rows,
            op_rates=typed.op_rates if request.op_rates is not None else old.op_rates,  # 4.24 (2026-11-25)
        )
        errors = master.parameter_violations(values) + DiscountBusiness().table_errors(tables)
        if errors:
            raise CostsheetValidationError("\n".join(errors), details=errors)
        self.repository.add(
            ParameterSet(
                effective_from=request.effective_from,
                values=values,
                tables=tables,
                created_by=access.display_name(self.current_user),
            )
        )
        self.logger.info("UC-09 parameter set effective %s saved", request.effective_from)
        return MessageResponse(message=f"Đã lưu bộ tham số hiệu lực từ {request.effective_from:%d/%m/%Y}.")

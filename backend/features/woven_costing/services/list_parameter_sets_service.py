"""UC-32 Xem các bộ tham số chung (2026-11-25: every set with its values by department and its two tables)."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.builders.parameter_builders import parameter_rows, parameter_set_detail
from backend.features.woven_costing.dto.master_dto import ParameterSetListResponse, ParameterSetRowDTO
from backend.features.woven_costing.repositories.norm_repository import ParameterSetRepository


class ListParameterSetsService(BaseService[EmptyRequest, ParameterSetListResponse]):
    def __init__(self, repository: ParameterSetRepository | None = None) -> None:
        self.repository = repository or ParameterSetRepository()

    def execute(self, request: EmptyRequest) -> ParameterSetListResponse:
        sets = self.repository.list_with_seed()
        self.logger.info("UC-32 %s parameter sets", len(sets))
        return ParameterSetListResponse(
            sets=[
                ParameterSetRowDTO(effective_from=s.effective_from, created_by=s.created_by, created_at=s.created_at)
                for s in sets
            ],  # fmt: skip
            latest=parameter_rows(sets[0].values),
            details=[parameter_set_detail(s) for s in sets],
        )

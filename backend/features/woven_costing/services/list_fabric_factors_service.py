"""UC-33 Xem hệ số theo mã hàng."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.builders.dto_builders import MasterRowsBuilder
from backend.features.woven_costing.dto.master_dto import FabricFactorListResponse
from backend.features.woven_costing.repositories.master_repository import FabricFactorRepository


class ListFabricFactorsService(BaseService[EmptyRequest, FabricFactorListResponse]):
    def __init__(self, repository: FabricFactorRepository | None = None) -> None:
        self.repository = repository or FabricFactorRepository()

    def execute(self, request: EmptyRequest) -> FabricFactorListResponse:
        factors = self.repository.list_with_seed()
        self.logger.info("UC-33 %s fabric factors", len(factors))
        return FabricFactorListResponse(rows=MasterRowsBuilder().factors(factors))

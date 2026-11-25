"""UC-04 Tra cứu mã vải."""

from backend.core.base import BaseService
from backend.features.woven_costing.builders.dto_builders import FabricDetailBuilder, FabricRowsBuilder
from backend.features.woven_costing.dto.fabric_dto import SearchFabricsRequest, SearchFabricsResponse
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository


class SearchFabricsService(BaseService[SearchFabricsRequest, SearchFabricsResponse]):
    def __init__(self, repository: FabricRepository | None = None) -> None:
        self.repository = repository or FabricRepository()

    def execute(self, request: SearchFabricsRequest) -> SearchFabricsResponse:
        keyword = request.keyword.strip().casefold()
        fabrics = [
            f
            for f in self.repository.list_all()
            if (not keyword or keyword in f"{f.tcfno} {f.fabric_name}".casefold())
            and (request.source is None or f.source == request.source)
            and (not request.missing_yarn_only or not f.yarns)
        ]
        fabrics.sort(key=lambda f: f.tcfno)
        detail = None
        if request.selected_tcfno:
            selected = self.repository.by_tcfno(request.selected_tcfno)
            detail = FabricDetailBuilder(selected).build() if selected else None
        self.logger.info("UC-04 keyword=%r source=%s -> %s fabrics", request.keyword, request.source, len(fabrics))
        return SearchFabricsResponse(total=len(fabrics), rows=FabricRowsBuilder(fabrics).build(), detail=detail)

"""UC-35 Đối chiếu giá cũ với giá app (BR-55)."""

from datetime import datetime

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.file_builders import LegacyComparisonFileBuilder
from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.dto.import_dto import (
    GetLegacyComparisonRequest,
    LegacyComparisonResponse,
    LegacyComparisonRowDTO,
)
from backend.features.yarn_costing.repositories.legacy_price_repository import LegacyPriceRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class GetLegacyComparisonService(BaseService[GetLegacyComparisonRequest, LegacyComparisonResponse]):
    def __init__(self, repository: LegacyPriceRepository | None = None) -> None:
        self.repository = repository or LegacyPriceRepository()
        self.analysis = AnalysisBusiness()

    def execute(self, request: GetLegacyComparisonRequest) -> LegacyComparisonResponse:
        prices = self.repository.for_import(request.import_id)
        yarns = {y.yarn_code: y for y in YarnRepository().list_all()}
        rows = []
        for p in prices:
            yarn = yarns.get(p.yarn_code)
            result = self.analysis.compare_legacy(p.yarn_code, p.total, yarn)
            new = yarn.regular_line.cost if yarn and yarn.regular_line and result.app_total is not None else None
            rows.append(
                LegacyComparisonRowDTO(
                    **result.model_dump(),
                    old_labor=p.cost.labor,
                    old_depreciation=p.cost.depreciation,
                    old_electricity=p.cost.electricity,
                    old_materials=p.cost.materials,
                    old_overhead=p.cost.overhead,
                    new_labor=new.labor if new else None,
                    new_depreciation=new.depreciation if new else None,
                    new_electricity=new.electricity if new else None,
                    new_materials=new.materials if new else None,
                    new_overhead=new.overhead if new else None,
                )
            )
        matched = sum(1 for r in rows if r.matched)
        not_priced = sum(1 for r in rows if r.app_total is None)
        items = [r for r in rows if r.app_total is not None and not r.matched] if request.only_mismatch else rows
        self.logger.info(
            "Legacy comparison %s: matched=%s mismatched=%s not priced=%s",
            request.import_id,
            matched,
            len(rows) - matched - not_priced,
            not_priced,
        )
        return LegacyComparisonResponse(
            items=items,
            matched_count=matched,
            mismatched_count=len(rows) - matched - not_priced,
            not_priced_count=not_priced,
            file=LegacyComparisonFileBuilder(items, datetime.now()).build(),
        )

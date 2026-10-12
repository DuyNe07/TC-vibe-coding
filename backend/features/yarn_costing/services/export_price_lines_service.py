"""UC-29 Xuất Excel bảng giá (5.4, theo bộ lọc đang chọn)."""

from datetime import date, datetime

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.yarn_costing.builders.dto_builders import stage_cost_dto
from backend.features.yarn_costing.builders.file_builders import PriceExportFileBuilder
from backend.features.yarn_costing.builders.price_rows_builder import PriceLineRowsBuilder
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.dto.price_dto import ExportPriceLinesRequest
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class ExportPriceLinesService(BaseService[ExportPriceLinesRequest, FileDownloadDTO]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.costing = CostingBusiness()

    def execute(self, request: ExportPriceLinesRequest) -> FileDownloadDTO:
        rate = self.costing.current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        yarns = self.repository.list_all()
        names = {(p.factory_code.value, p.code): p.name for p in PackagingTypeRepository().list_all()}
        rows = PriceLineRowsBuilder(
            yarns, request, rate.rate if rate else None, names, StageRepository().list_all()
        ).build()
        codes = list(dict.fromkeys(r.yarn_code for r in rows))
        by_code = {y.yarn_code: y for y in yarns}
        details = [(c, by_code[c].yarn_name, stage_cost_dto(d)) for c in codes for d in by_code[c].stage_details]
        self.logger.info("Export price list: %s rows, %s stage details", len(rows), len(details))
        return PriceExportFileBuilder(rows, details, datetime.now()).build()

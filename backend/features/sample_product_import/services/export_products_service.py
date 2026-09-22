"""UC-05: export the (filtered) product list to Excel."""

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.sample_product_import.builders.product_builders import ProductExportFileBuilder
from backend.features.sample_product_import.business.stock_business import ProductStockBusiness
from backend.features.sample_product_import.dto.product_dto import ExportProductsRequest
from backend.features.sample_product_import.repositories.product_repository import ProductRepository


class ExportProductsService(BaseService[ExportProductsRequest, FileDownloadDTO]):
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()
        self.business = ProductStockBusiness()

    def execute(self, request: ExportProductsRequest) -> FileDownloadDTO:
        products = self.business.filter_by_status(self.repository.search(request.keyword), request.stock_status)
        self.logger.info("Exporting %s products to Excel", len(products))
        return ProductExportFileBuilder([(p, self.business.classify(p)) for p in products]).build()

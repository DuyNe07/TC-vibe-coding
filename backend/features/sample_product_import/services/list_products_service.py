"""UC-04: search products with stock status and totals."""

from backend.core.base import BaseService
from backend.features.sample_product_import.builders.product_builders import ProductListResponseBuilder
from backend.features.sample_product_import.business.stock_business import ProductStockBusiness
from backend.features.sample_product_import.dto.product_dto import ListProductsRequest, ProductListResponse
from backend.features.sample_product_import.repositories.product_repository import ProductRepository


class ListProductsService(BaseService[ListProductsRequest, ProductListResponse]):
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()
        self.business = ProductStockBusiness()

    def execute(self, request: ListProductsRequest) -> ProductListResponse:
        products = self.business.filter_by_status(self.repository.search(request.keyword), request.stock_status)
        self.logger.info(
            "Found %s products (keyword=%r, status=%s)", len(products), request.keyword, request.stock_status
        )
        classified = [(p, self.business.classify(p)) for p in products]
        return ProductListResponseBuilder(classified, self.business.summarize(products)).build()

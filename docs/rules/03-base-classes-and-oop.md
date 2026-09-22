# 03 - Base Classes and OOP

Every class you write inherits the base class of its folder. Import bases ONLY from `backend.core.base`.
`tests/architecture/test_inheritance.py` fails if a class does not inherit the right base.

| Folder | Must inherit | Import |
|---|---|---|
| `models/` | `BaseEntity` (has id, timestamps), `BaseValueObject` (immutable), or `StrEnum` | `backend.core.base` |
| `dto/` | `BaseRequestDTO`, `BaseResponseDTO`, `BaseDTO` (nested), or `StrEnum` | `backend.core.base` |
| `business/` | `BaseBusinessRule[T]` (one rule) or `BaseBusiness[T]` (a capability) | `backend.core.base` |
| `builders/` | `BaseBuilder[Output]` | `backend.core.base` |
| `repositories/` | `JsonFileRepository[Entity]` (or `InMemoryRepository` for tests) | `backend.core.base` |
| `services/` | `BaseService[Request, Response]` | `backend.core.base` |
| `controllers/` | `BaseController` | `backend.core.base` |
| `exceptions.py` | `AppError` or a subclass | `backend.core.exceptions` |
| frontend `pages/` | `BasePage` | `frontend.core.base_page` |

## Examples (from `sample_product_import`)

### Model
```python
class Product(BaseEntity):
    code: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=0)
    unit_price: Decimal = Field(gt=0)

    @property
    def total_value(self) -> Decimal:  # self-contained derived value: OK in a model
        return self.unit_price * self.quantity
```

### DTO
```python
class ListProductsRequest(BaseRequestDTO):
    keyword: str = ""
    stock_status: StockStatus | None = None


class ProductListResponse(BaseResponseDTO):
    items: list[ProductDTO]
    summary: StockSummaryDTO
```

### Business rule + business class
```python
class UnitPriceRule(BaseBusinessRule[ImportRow]):
    code = "BR-04"  # MUST exist in docs/business/<key>.md
    message = "Đơn giá bắt buộc và phải lớn hơn 0."  # shown to the user
    field = "unit_price"

    def is_satisfied_by(self, target: ImportRow) -> bool:
        return target.unit_price is not None and target.unit_price > 0


class ProductImportBusiness(BaseBusiness[ImportRow]):
    def rules(self):  # used by collect_violations / ensure_valid
        return (ProductCodeRule(), UnitPriceRule())
```

### Repository
```python
class ProductRepository(JsonFileRepository[Product]):
    storage_file = "products.json"  # -> data/<feature_key>/products.json

    def index_by_code(self) -> dict[str, Product]:
        return {p.code: p for p in self.list_all()}
```
Inherited API: `get`, `get_or_raise`, `list_all`, `find`, `find_one`, `exists`, `count`, `add`, `update`,
`save`, `save_many`, `delete`, `clear`.

### Builder
```python
class ProductExportFileBuilder(BaseBuilder[FileDownloadDTO]):
    def __init__(self, products: list[Product]) -> None:
        self.products = products

    def build(self) -> FileDownloadDTO:
        rows = [{"Mã SP": p.code, "Số lượng": p.quantity} for p in self.products]
        return FileDownloadDTO(
            filename="ton-kho.xlsx", content=ExcelWriter().write({"Tồn kho": rows}), mime_type=MimeType.XLSX
        )
```

### Service (one use case)
```python
class ListProductsService(BaseService[ListProductsRequest, ProductListResponse]):
    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()
        self.business = ProductStockBusiness()

    def execute(self, request: ListProductsRequest) -> ProductListResponse:
        products = self.business.filter_by_status(self.repository.search(request.keyword), request.stock_status)
        self.logger.info("Found %s products for keyword=%r", len(products), request.keyword)
        return ProductListResponseBuilder(products, self.business.summarize(products)).build()
```
`handle()` (called by the controller) validates the request, logs start/end/errors and calls `execute()`.
You implement `execute()` only; overriding `handle()` raises an error.

### Controller (top layer, one per feature) + package export
```python
# backend/features/sample_product_import/controllers/sample_product_import_controller.py
class SampleProductImportController(BaseController):
    def list_products(self, request: ListProductsRequest) -> ProductListResponse:
        """UC-04 Tra cứu sản phẩm + tồn kho."""
        return ListProductsService().handle(request)


# backend/features/sample_product_import/__init__.py
from backend.features.sample_product_import.controllers.sample_product_import_controller import (
    SampleProductImportController,
)

__all__ = ["SampleProductImportController"]

# page
products = gateway.open(SampleProductImportController)
data = products.list_products(ListProductsRequest(keyword="A"))
```

## OOP rules
1. Inherit, don't copy: reuse base behaviour (`ensure_valid`, repository CRUD, `handle`, `BasePage.run`).
2. Template methods are fixed: never override `BaseService.handle` or `BasePage.run`.
3. One class = one responsibility. One service per file. One rule per rule class.
4. Composition for collaborators: services receive repositories/builders/business objects; they don't inherit them.
5. No module-level mutable state; no singletons in features.
6. Type hints everywhere; generics declare their types (`BaseService[Req, Res]`, `JsonFileRepository[Entity]`).

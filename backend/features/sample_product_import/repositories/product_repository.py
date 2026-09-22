from backend.core.base import JsonFileRepository
from backend.features.sample_product_import.models.product import Product


class ProductRepository(JsonFileRepository[Product]):
    """Stored in data/sample_product_import/products.json."""

    storage_file = "products.json"

    def index_by_code(self) -> dict[str, Product]:
        return {p.code: p for p in self.list_all()}

    def search(self, keyword: str = "") -> list[Product]:
        needle = keyword.strip().lower()
        items = [p for p in self.list_all() if not needle or needle in f"{p.code} {p.name}".lower()]
        return sorted(items, key=lambda p: p.code)

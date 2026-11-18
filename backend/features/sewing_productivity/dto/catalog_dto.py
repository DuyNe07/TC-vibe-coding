"""UC-21 to UC-25: the 4 catalogs. Row fields accept None, so an empty cell reaches BR-47 and shows its message."""

from pydantic import ConfigDict

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.dto.line_detail_dto import LineStrengthDTO


class ProductGroupRowDTO(BaseDTO):
    product_name: str | None = None
    product_group: str | None = None


class CustomerGroupRowDTO(BaseDTO):
    customer_name: str | None = None
    customer_group: str | None = None


class LineMappingRowDTO(BaseDTO):
    old_line: str | None = None
    new_line: str | None = None


class StyleProductRowDTO(BaseDTO):
    """A style typed as a number in the table stays text."""

    model_config = ConfigDict(coerce_numbers_to_str=True)

    style: str | None = None
    product_name: str | None = None


class UnclassifiedProductDTO(BaseDTO):
    product_name: str
    row_count: int


class CustomerNameDTO(BaseDTO):
    customer_name: str
    customer_group: str
    row_count: int


class StyleWithoutProductDTO(BaseDTO):
    style: str
    customer_name: str
    row_count: int


class CatalogsResponse(BaseResponseDTO):
    product_groups: list[ProductGroupRowDTO]
    customer_groups: list[CustomerGroupRowDTO]
    line_mappings: list[LineMappingRowDTO]
    style_products: list[StyleProductRowDTO]
    unclassified_products: list[UnclassifiedProductDTO]
    customer_names: list[CustomerNameDTO]
    styles_without_product: list[StyleWithoutProductDTO]
    line_strengths: list[LineStrengthDTO] = []  # UC-34 (thêm 2026-11-12), read only


class SaveProductGroupsRequest(BaseRequestDTO):
    rows: list[ProductGroupRowDTO] = []


class SaveCustomerGroupsRequest(BaseRequestDTO):
    rows: list[CustomerGroupRowDTO] = []


class SaveLineMappingsRequest(BaseRequestDTO):
    rows: list[LineMappingRowDTO] = []


class SaveStyleProductsRequest(BaseRequestDTO):
    rows: list[StyleProductRowDTO] = []


class SaveCatalogResponse(BaseResponseDTO):
    message: str

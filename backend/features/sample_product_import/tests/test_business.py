from decimal import Decimal

import pytest

from backend.core.exceptions import BusinessRuleViolation
from backend.features.sample_product_import.business.import_business import ProductImportBusiness
from backend.features.sample_product_import.business.stock_business import ProductStockBusiness
from backend.features.sample_product_import.models.import_row import ImportAction, ImportRow
from backend.features.sample_product_import.models.product import Product, StockStatus


def row(n: int = 2, **overrides) -> ImportRow:
    values = {"row_number": n, "code": "SP-01", "name": "Áo", "quantity": Decimal(5), "unit_price": Decimal(10)}
    return ImportRow(**{**values, **overrides})


@pytest.mark.parametrize(
    ("overrides", "rule_code"),
    [
        ({"code": ""}, "BR-01"),
        ({"code": "sp 01"}, "BR-01"),
        ({"name": ""}, "BR-02"),
        ({"quantity": None}, "BR-03"),
        ({"quantity": Decimal("1.5")}, "BR-03"),
        ({"quantity": Decimal(-1)}, "BR-03"),
        ({"unit_price": Decimal(0)}, "BR-04"),
    ],
)
def test_row_rules(overrides, rule_code) -> None:
    violations = ProductImportBusiness().collect_violations(row(**overrides))
    assert [v.rule_code for v in violations] == [rule_code]


def test_duplicates_rejected_and_existing_codes_updated() -> None:
    rows = [row(2, code="A"), row(3, code="A"), row(4, code="B"), row(5, code="C")]
    evaluation = ProductImportBusiness().evaluate(rows, existing_codes={"B"})
    assert [r.action for r in evaluation.rows] == [
        ImportAction.REJECT,
        ImportAction.REJECT,
        ImportAction.UPDATE,
        ImportAction.CREATE,
    ]
    assert evaluation.rows[0].violations[0].rule_code == "BR-05"


def test_to_product_keeps_id_when_updating() -> None:
    existing = Product(code="A", name="Cũ", quantity=1, unit_price=Decimal(1))
    updated = ProductImportBusiness().to_product(row(code="A", name="Mới"), existing)
    assert updated.id == existing.id and updated.name == "Mới"


def test_empty_file_is_rejected() -> None:
    with pytest.raises(BusinessRuleViolation):
        ProductImportBusiness().ensure_row_limit([])


@pytest.mark.parametrize(
    ("quantity", "status"), [(0, StockStatus.OUT_OF_STOCK), (9, StockStatus.LOW), (10, StockStatus.IN_STOCK)]
)
def test_stock_status(quantity, status) -> None:
    product = Product(code="A", name="A", quantity=quantity, unit_price=Decimal(2))
    assert ProductStockBusiness().classify(product) == status


def test_summary_totals() -> None:
    products = [
        Product(code="A", name="A", quantity=2, unit_price=Decimal(3)),
        Product(code="B", name="B", quantity=0, unit_price=Decimal(5)),
    ]
    summary = ProductStockBusiness().summarize(products)
    assert (summary.total_quantity, summary.total_value, summary.out_of_stock) == (2, Decimal(6), 1)

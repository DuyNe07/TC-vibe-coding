"""BR-10 specs, BR-13 shrinkage, BR-16 % B/C, BR-18 quantities, BR-23 quantity factor."""

from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.enums import (
    NO_DYEING_FORMS,
    NO_WEAVING_FORMS,
    OrderType,
    SaleForm,
    ShrinkageException,
)
from backend.features.woven_costing.models.fabric import FabricSpecs
from backend.features.woven_costing.models.parameter_set import ParameterValues, legacy_tables
from backend.features.woven_costing.models.parameter_tables import ParameterTables

THOUSAND = Decimal(1000)


class QuantityBusiness(BaseBusiness[Costsheet]):
    def meters_per_kg(self, g_per_m: Decimal | None) -> Decimal:
        """BR-10: m/kg = 1000 / g/m (0 when g/m is empty or 0)."""
        return div(THOUSAND, num(g_per_m))

    def missing_specs(self, specs: FabricSpecs, sale_form: SaleForm | None) -> list[str]:
        """BR-10: specs needed by the calculation that are empty or 0."""
        needed = {
            "khổ mộc": specs.greige_width_cm,
            "mật độ dọc mộc": specs.greige_warp_density,
            "mật độ ngang mộc": specs.greige_weft_density,
            "g/m mộc": specs.greige_g_per_m,
        }
        if sale_form is not None and sale_form not in NO_DYEING_FORMS:
            needed["g/m thành phẩm"] = specs.finished_g_per_m
        return [label for label, value in needed.items() if not value]

    def shrinkage(self, costsheet: Costsheet) -> Decimal:
        """BR-13: (weft density TP - weft density greige) / weft density TP; 0 for Mộc, no TP density or
        "Mộc khách đã ổn định"."""
        specs = costsheet.fabric_snapshot.specs
        finished = num(specs.finished_weft_density)
        if (
            costsheet.sale_form in NO_DYEING_FORMS
            or finished == 0
            or costsheet.shrinkage_exception == ShrinkageException.STABLE_GREIGE
        ):
            return ZERO
        return (finished - num(specs.greige_weft_density)) / finished

    def bc_rates(
        self, sale_form: SaleForm | None, params: ParameterValues, tables: ParameterTables | None = None
    ) -> tuple[Decimal, Decimal]:
        """BR-16 (2026-11-25): (% B/C mộc, % B/C TP) from the 4.6.2 row of the sale form."""
        return DiscountBusiness().bc_rates(tables or legacy_tables(params), sale_form)

    def finished_meters_needed(self, order_meters: Decimal, finished_bc: Decimal) -> Decimal:
        """BR-18: order meters / (1 - % B/C TP)."""
        return div(order_meters, ONE - finished_bc)

    def greige_meters(
        self,
        finished_needed: Decimal,
        dye_loss: Decimal,
        shrinkage: Decimal,
        greige_bc: Decimal,
        sale_form: SaleForm | None,
    ) -> Decimal:
        """BR-18: finished needed / (1 - dye loss) / (1 - shrinkage) [/ (1 - % B/C mộc) unless Vải Nhuộm]."""
        meters = div(div(finished_needed, ONE - dye_loss), ONE - shrinkage)
        return meters if sale_form in NO_WEAVING_FORMS else div(meters, ONE - greige_bc)

    def quantity_factor(
        self,
        greige_meters: Decimal,
        sale_form: SaleForm | None,
        order_type: OrderType | None,
        p: ParameterValues,
        tables: ParameterTables | None = None,
    ) -> Decimal:
        """BR-23 (2026-11-25): quantity factor of the weaving department from the 4.6.1 Dệt rows by greige meters."""
        return DiscountBusiness().weaving(tables or legacy_tables(p), greige_meters, sale_form, order_type).factor

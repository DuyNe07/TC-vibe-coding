"""CostsheetInputRequest (cells typed on Screen 2) -> the input fields of a Costsheet entity."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.woven_costing.constants import (
    MAX_COGS_LINES,
    MAX_HCM_FEATURES,
    MAX_HCM_SPECIAL_COSTS,
    MAX_HCM_STAGES,
    MAX_OUTSOURCING,
    MAX_TCDN_FEATURES,
    MAX_TCDN_STAGES,
    MAX_TWIST_LINES,
)
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetInputDTO,
    ExtraCostDTO,
    HcmDyeingInputDTO,
    PriceInputDTO,
    TcdnDyeingInputDTO,
)
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_input import (
    CogsLine,
    ExtraCost,
    HcmDyeingInput,
    NamedCost,
    PriceInput,
    TcdnDyeingInput,
    TcdnOutsourcing,
    TcdnStageInput,
    TwistLine,
    WeavingInput,
    YarnLine,
)
from backend.features.woven_costing.models.enums import YarnDirection

ZERO = Decimal(0)
ITEM_NAMES = ("chemical", "labor", "depreciation", "power", "fuel", "material", "overhead")
TWIST_DIRECTIONS = ("Dọc", "Ngang")


def extra_cost(dto: ExtraCostDTO | None) -> ExtraCost | None:
    if dto is None:
        return None
    items = CostItems(**{name: getattr(dto, name) or ZERO for name in ITEM_NAMES})
    if not dto.name and items.total == 0:
        return None
    return ExtraCost(name=dto.name, items=items)


def hcm_input(dto: HcmDyeingInputDTO) -> HcmDyeingInput:
    return HcmDyeingInput(
        dye_material=dto.dye_material,
        color_level=dto.color_level,
        blend_ratios=[r or ZERO for r in (list(dto.blend_ratios) + [ZERO] * 5)[:5]],
        width_type=dto.width_type if dto.width_type in (1, 2, 3) else 1,
        dye_loss_rate=dto.dye_loss_rate,
        special_stages=[s for s in dto.special_stages if s][:MAX_HCM_STAGES],
        special_features=[s for s in dto.special_features if s][:MAX_HCM_FEATURES],
        special_costs=[NamedCost(name=c.name, amount=c.amount) for c in dto.special_costs if c.name or c.amount][
            :MAX_HCM_SPECIAL_COSTS
        ],
        extra_cost=extra_cost(dto.extra_cost),
        extra_cost_reason=dto.extra_cost_reason,
        outsourcing_lines=[
            NamedCost(name=c.name, amount=c.amount) for c in dto.outsourcing_lines if c.name or c.amount
        ][:MAX_OUTSOURCING],  # fmt: skip
    )


def tcdn_input(dto: TcdnDyeingInputDTO) -> TcdnDyeingInput:
    return TcdnDyeingInput(
        dye_material=dto.dye_material,
        color_level=dto.color_level,
        blend_ratios=[r or ZERO for r in (list(dto.blend_ratios) + [ZERO] * 5)[:5]],
        special_dye=dto.special_dye,
        special_dye_chemical_price=dto.special_dye_chemical_price,
        wr_chemical=dto.wr_chemical,
        extra_stages=[
            TcdnStageInput(name=s.name, chemical_price=s.chemical_price, repeat_count=min(max(s.repeat_count, 0), 9))
            for s in dto.extra_stages
            if s.name
        ][:MAX_TCDN_STAGES],  # fmt: skip
        special_features=[NamedCost(name=f.name, amount=f.amount) for f in dto.special_features if f.name][
            :MAX_TCDN_FEATURES
        ],
        extra_cost_type=dto.extra_cost_type,
        extra_cost_loss_rate=dto.extra_cost_loss_rate,
        extra_cost=extra_cost(dto.extra_cost),
        extra_cost_reason=dto.extra_cost_reason,
        outsourcing_lines=[
            TcdnOutsourcing(name=o.name, amount=o.amount, loss_rate=o.loss_rate)
            for o in dto.outsourcing_lines
            if o.name or o.amount
        ][:MAX_OUTSOURCING],  # fmt: skip
    )


def price_input(dto: PriceInputDTO) -> PriceInput:
    return PriceInput(
        sell_price_currency=dto.sell_price_currency,
        sell_price_input=dto.sell_price_input,
        cogs_extra_lines=[
            CogsLine(name=c.name, amount=c.amount, note=c.note) for c in dto.cogs_extra_lines if c.name or c.amount
        ][:MAX_COGS_LINES],  # fmt: skip
        commission=dto.commission or ZERO,
        freight_insurance=dto.freight_insurance or ZERO,
        interest_cost=dto.interest_cost or ZERO,
        ship_date=dto.ship_date,
    )


class CostsheetInputBuilder(BaseBuilder[Costsheet]):
    """Applies the typed cells to a costsheet. A yarn price that changes (or "Xác nhận giá sợi hôm nay") gets
    today as price date (BR-44). Weft lines never keep the Hồ tick (BR-09)."""

    def __init__(self, sheet: Costsheet, data: CostsheetInputDTO, today: date, confirm_prices: bool = False) -> None:
        self.sheet = sheet
        self.data = data
        self.today = today
        self.confirm = confirm_prices

    def yarn_lines(self) -> list[YarnLine]:
        typed = {(y.direction, y.seq): y for y in self.data.yarn_lines}
        lines = []
        for line in self.sheet.yarn_lines:
            new = typed.get((line.direction, line.seq))
            if new is None:
                lines.append(line.model_copy(update={"price_entered_on": self.today}) if self.confirm else line)
                continue
            changed = new.price_input != line.price_input or new.price_currency != line.price_currency
            entered_on = (
                self.today if (changed or self.confirm) and new.price_input is not None else line.price_entered_on
            )
            lines.append(
                line.model_copy(
                    update={
                        "price_currency": new.price_currency,
                        "price_input": new.price_input,
                        "price_entered_on": entered_on,
                        "waste_rate": new.waste_rate if new.waste_rate is not None else ZERO,
                        "is_twisted": new.is_twisted,
                        "is_sized": new.is_sized and line.direction == YarnDirection.WARP,
                    }
                )
            )
        return lines

    def build(self) -> Costsheet:
        d = self.data
        twist = [
            TwistLine(
                direction=t.direction if t.direction in TWIST_DIRECTIONS else TWIST_DIRECTIONS[0],
                fiber_system=t.fiber_system,
                count=t.count,
                twist=t.twist,
                quantity_kg=t.quantity_kg,
                fiber_suggested=t.fiber_suggested,
                suggested=t.suggested,
                suggestion_key=t.suggestion_key,
            )  # fmt: skip
            for t in d.twist_lines
            if t.count or t.quantity_kg
        ]
        offered = [TwistLine(**t.model_dump()) for t in d.twist_suggestions]
        dirs = {
            direction: [t for t in twist if t.direction == direction][:MAX_TWIST_LINES]
            for direction in TWIST_DIRECTIONS
        }
        update = {
            "dye_plant": d.dye_plant,
            "customer_name": d.customer_name or self.sheet.customer_name,
            "market": d.market,
            "order_type": d.order_type,
            "style": d.style,
            "sale_form": d.sale_form,
            "greige_buy_price": d.greige_buy_price,
            "delivery_date": d.delivery_date,
            "costing_date": d.costing_date or self.sheet.costing_date,
            "tcfno": (d.tcfno or self.sheet.tcfno).strip().upper(),
            "order_meters": d.order_meters,
            "price_type": d.price_type,
            "shrinkage_exception": d.shrinkage_exception,
            "shrinkage_reason": d.shrinkage_reason,
            "note": d.note,
            "yarn_lines": self.yarn_lines(),
            "twist_lines": dirs[TWIST_DIRECTIONS[0]] + dirs[TWIST_DIRECTIONS[1]],
            "twist_lines_suggested": self.sheet.twist_lines_suggested or d.twist_lines_suggested,
            # BR-86: the suggestions shown with the cells typed (the working copy may not be saved yet)
            "twist_lines_live": self.sheet.twist_lines_live or d.twist_lines_live,
            "twist_suggestions": offered,
            "twist_suggestion_skips": sorted(set(self.sheet.twist_suggestion_skips) | set(d.twist_suggestion_skips)),
            "weaving": WeavingInput(**d.weaving.model_dump()),
            "hcm_dyeing": hcm_input(d.hcm_dyeing),
            "tcdn_dyeing": tcdn_input(d.tcdn_dyeing),
            "price": price_input(d.price),
        }
        return self.sheet.model_copy(update=update)

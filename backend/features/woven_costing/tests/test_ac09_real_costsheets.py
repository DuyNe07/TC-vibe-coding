"""AC-09: the 4 real costsheets of "File kết quả" give the same GP% and OP% (tolerance 0.01 percentage point).

Inputs are typed from the files (header, specs I9..J13, yarn rows C/D/E/F/K/O/P, Se rows G/H/I/J, G70/G72/G73,
dyeing inputs, sell price). Norms = the initial (seed) norm set = the tables of the official workbooks.

Data difference of the files: their "DM Se 2025" sheet looks the singeing (bấm đốt) efficiency up with XLOOKUP, which
the Excel used to save them does not know (#NAME?): the saved results contain NO singeing cost. To compare with the
same norm tables as the files, the BẤM ĐỐT - CARBON rates are set to 0 here (BR-20 keeps the singeing cost; it has
its own unit test in test_calculation.py).
"""

from datetime import date
from decimal import Decimal

import pytest

from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.constants import STAGE_SINGEING
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet import Costsheet, FabricSnapshot
from backend.features.woven_costing.models.costsheet_input import (
    HcmDyeingInput,
    PriceInput,
    TcdnDyeingInput,
    TcdnStageInput,
    TwistLine,
    WeavingInput,
    YarnLine,
)
from backend.features.woven_costing.models.enums import (
    Currency,
    DyePlant,
    FabricSource,
    FiberSystem,
    OrderType,
    SaleForm,
    YarnDirection,
)
from backend.features.woven_costing.models.fabric import FabricSpecs, FabricYarn
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.models.parameter_set import ParameterValues

D = Decimal
W, F = YarnDirection.WARP, YarnDirection.WEFT


def _tables():
    tables = initial_tables()
    rates = [
        r.model_copy(update={"rates": CostItems()}) if r.stage == STAGE_SINGEING else r for r in tables.minute_rates
    ]
    return tables.model_copy(update={"minute_rates": rates})


def _yarn(direction, seq, name, tpm, ratio, currency, price, waste, se, ho, on):
    yarn = FabricYarn(direction=direction, seq=seq, yarn_name=name, raw_yarn_name=name, rate=D(ratio) * 100,
                      raw_rate=D(100), twist_tpm=tpm)  # fmt: skip
    line = YarnLine(
        direction=direction, seq=seq, yarn_name=name, twist_tpm=tpm, ratio=yarn.ratio, price_currency=currency,
        price_input=D(price), price_entered_on=on, waste_rate=D(waste), is_twisted=se, is_sized=ho,
    )  # fmt: skip
    return yarn, line


def _sheet(*, plant, sale_form, order_type, meters, rate, on, specs, yarns, twists, weaving, hcm=None, tcdn=None,
           price):  # fmt: skip
    pairs = [_yarn(*y, on) for y in yarns]
    return Costsheet(
        costsheet_no="CS-TEST-2026-00001",
        dye_plant=plant,
        sale_form=sale_form,
        order_type=order_type,
        costing_date=on,
        tcfno="AC09000000",
        order_meters=D(meters),
        exchange_rate=D(rate),
        fabric_snapshot=FabricSnapshot(
            tcfno="AC09000000", source=FabricSource.PEACE, specs=specs, yarns=[p[0] for p in pairs]
        ),  # fmt: skip
        yarn_lines=[p[1] for p in pairs],
        twist_lines=[
            TwistLine(direction=d, fiber_system=s, count=c, twist=t, quantity_kg=D(q)) for d, s, c, t, q in twists
        ],
        weaving=weaving,
        hcm_dyeing=hcm or HcmDyeingInput(),
        tcdn_dyeing=tcdn or TcdnDyeingInput(),
        price=price,
    )


def _specs(gw, gweft, gwarp, ggm, ggsm, fw=None, fweft=None, fwarp=None, fgm=None, fgsm=None):
    def v(x: object) -> Decimal | None:
        return None if x is None else D(str(x))

    return FabricSpecs(
        greige_width_cm=v(gw), greige_weft_density=v(gweft), greige_warp_density=v(gwarp), greige_g_per_m=v(ggm),
        greige_gsm=v(ggsm), finished_width_cm=v(fw), finished_weft_density=v(fweft), finished_warp_density=v(fwarp),
        finished_g_per_m=v(fgm), finished_gsm=v(fgsm), warping_loss_rate=D("0.10"),
    )  # fmt: skip


USD, VND = Currency.USD, Currency.VND
FIL, SPUN = FiberSystem.FILAMENT, FiberSystem.SPUN

R1 = _sheet(
    plant=DyePlant.HCM, sale_form=SaleForm.GREIGE, order_type=OrderType.TRIAL, meters=31, rate=26080,
    on=date(2026, 9, 7), specs=_specs(175, 252, 431, 217, 124),
    yarns=[
        (W, 1, "TC 34/1 (65/35)", "", "0.6367", USD, "5.29", "0.03", False, True),
        (W, 2, "DTY75D/36F/1HIM", "400T/M", "0.0066", USD, "2", "0.16", True, True),
        (W, 3, "WHITECACBON20D/3F/1", "400T/M", "0.0017", USD, "164", "0.16", True, True),
        (F, 1, "DTY 150D/48F/1 SIM", "", "0.355", USD, "1.97", "0", False, False),
    ],
    twists=[("Dọc", FIL, "75D + CB", 400, "0.07169689451840895")],
    weaving=WeavingInput(size_material="TC", warping_band="Không"),
    price=PriceInput(sell_price_currency=USD, sell_price_input=D("2.13")),
)  # fmt: skip

R2 = _sheet(
    plant=DyePlant.TCDN, sale_form=SaleForm.FINISHED, order_type=OrderType.PRODUCTION, meters=10000, rate=26790,
    on=date(2026, 8, 7), specs=_specs(165, 484, 524, 172, 104, 152, 539, 569, 175, 115),
    yarns=[
        (W, 1, "DTY 75D/72F/1 SIM FD", "", "0.4877", USD, "3.95", "0.02", False, True),
        (W, 2, "WHITECACBON20D/3F/1", "400T/M", "0.0011", USD, "164", "0.16", True, True),
        (W, 3, "DTY75D/72F/1SIMFD", "400T/M", "0.0041", USD, "3.95", "0.16", True, True),
        (F, 1, "DTY 75D/72F/1 SIM FD", "", "0.3381", USD, "3.95", "0", False, False),
        (F, 2, "DTY 150D/48F/1 SIM 1H", "", "0.169", VND, "47000", "0", False, False),
    ],
    twists=[("Dọc", FIL, "75D + CB", 400, "14.024299591733802")],
    weaving=WeavingInput(size_material="DTY", warping_band="Không"),
    tcdn=TcdnDyeingInput(
        dye_material="Poly", color_level="White",
        extra_stages=[TcdnStageInput(name="Soaping", chemical_price=D(362)), TcdnStageInput(name="Setting")],
    ),  # fmt: skip
    price=PriceInput(sell_price_currency=USD, sell_price_input=D("2.26")),
)  # fmt: skip

R3 = _sheet(
    plant=DyePlant.HCM, sale_form=SaleForm.FINISHED, order_type=OrderType.PRODUCTION, meters=5000, rate=26254,
    on=date(2026, 6, 30), specs=_specs(174, 242, 403, 351, 202, 150, 255, 467, 359, 239),
    yarns=[
        (W, 1, "TC45/1(65/35)", "800T/M", "0.28625", VND, "78300", "0.04", True, False),
        (W, 2, "TC45/2(65/35)", "800T/M", "0.28625", VND, "78300", "0.04", True, False),
        (F, 1, "DTY150D/48F/1HIM", "170T/M", "0.4275", USD, "1.92", "0", True, False),
    ],
    twists=[("Dọc", SPUN, "45/2", 800, "1249.6461911112356"), ("Ngang", FIL, "150D", 170, "930.0043370871552")],
    weaving=WeavingInput(warping_band="Có", cone_count_1="150D"),
    hcm=HcmDyeingInput(dye_material="TC/CVC/TR thường", color_level="Đậm", dye_loss_rate=D("0.024")),
    price=PriceInput(sell_price_currency=VND, sell_price_input=D(71000)),
)  # fmt: skip

R4 = _sheet(
    plant=DyePlant.TCDN, sale_form=SaleForm.FINISHED, order_type=OrderType.PRODUCTION, meters=8278, rate=26286,
    on=date(2026, 7, 7), specs=_specs(163, 326, 488, 161, 99, 151, 382, 526, 180, 119),
    yarns=[
        (W, 1, "DTY75D/36F/1HIM", "400T/M", "0.00320005", USD, "2.05", "0.07", True, False),
        (W, 2, "DTY75D/36F/1HIM", "400T/M", "0.4464", USD, "2.05", "0.16", True, False),
        (W, 3, "WHITECACBON20D/3F/1", "400T/M", "0.00089995", VND, "4440231.12", "0.16", True, False),
        (F, 1, "CM 40/1 COMPACT", "", "0.1695", VND, "103000", "0", False, False),
        (F, 2, "DTY 150D/48F/1 HIM", "", "0.38", USD, "1.92", "0", False, False),
    ],
    twists=[("Dọc", FIL, "75D/2", 400, "957.2739912637187"), ("Dọc", FIL, "75D + CB", 400, "8.122167280349693")],
    weaving=WeavingInput(warping_band="Có"),
    tcdn=TcdnDyeingInput(dye_material="Cotton/Poly", color_level="Dark"),
    price=PriceInput(sell_price_currency=VND, sell_price_input=D(51500)),
)  # fmt: skip

CASES = [
    ("EM3579", R1, "19.17", "11.01"),
    ("TM01510696", R3, "15.20", "6.64"),
    ("EF3532", R2, "19.99", "11.92"),
    ("EM04150201", R4, "23.02", "15.26"),
]


@pytest.mark.parametrize(("name", "sheet", "gp", "op"), CASES, ids=[c[0] for c in CASES])
def test_ac09_real_costsheets_match_excel(name: str, sheet: Costsheet, gp: str, op: str) -> None:
    context = CostingContext(costsheet=sheet, tables=_tables(), params=ParameterValues())
    result = CostingBusiness().calculate(context)
    assert result.calculated
    assert abs(result.gp_pct * 100 - D(gp)) <= D("0.01"), (name, result.gp_pct)
    assert abs(result.op_pct * 100 - D(op)) <= D("0.01"), (name, result.op_pct)

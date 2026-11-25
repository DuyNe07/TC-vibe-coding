"""4.6 Bộ tham số chung (values + effective date) and 4.18 values overridden on a costsheet."""

from datetime import date
from decimal import Decimal
from typing import Final

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.woven_costing.models.enums import DiscountCondition, DiscountDepartment, ParamGroup, SaleForm
from backend.features.woven_costing.models.parameter_tables import (
    BcRow,
    DiscountRow,
    ParameterTables,
    company_weaving_rows,
)

D = Decimal
# BR-23 / BR-25 / BR-26 limits of the single values used before 2026-11-25 (m mộc, m TP)
QF_5000, QF_10000, QF_20000, QF_50000, QF_100000 = D(5000), D(10000), D(20000), D(50000), D(100000)
TCDN_LARGE_METERS, TCDN_DYE_SMALL_METERS, TCDN_PARTIAL_SMALL_METERS = D(50000), D(150), D(100)


class ParameterValues(BaseValueObject):
    """Every number of 4.6 (weft_loss_table and quantity_factor_table spread into one field per cell)."""

    sa_rate: Decimal = D("0.1009")
    vat_rate: Decimal = D("0.08")
    warp_loss_base: Decimal = D("0.0082")
    warp_loss_twist: Decimal = D("0.01")
    warp_loss_size: Decimal = D("0.0206")
    weft_loss_twist_130: Decimal = D("0.0677")
    weft_loss_twist_175: Decimal = D("0.0547")
    weft_loss_twist_215: Decimal = D("0.0477")
    weft_loss_plain_130: Decimal = D("0.0575")
    weft_loss_plain_175: Decimal = D("0.0445")
    weft_loss_plain_215: Decimal = D("0.0375")
    twist_loss_offset: Decimal = D("0.01")
    greige_bc_rate_grey: Decimal = D("0.04")
    greige_bc_rate_other: Decimal = D("0.05")
    finished_bc_rate_grey: Decimal = D("0")
    finished_bc_rate_other: Decimal = D("0.04")
    yarn_waste_price: Decimal = D("15000")
    bc_fabric_price: Decimal = D("5000")
    qf_below_5000: Decimal = D("1.1")
    qf_at_5000: Decimal = D("1.05")
    qf_10000_20000: Decimal = D("1")
    qf_after_20000: Decimal = D("0.95")
    qf_at_50000: Decimal = D("0.92")
    qf_from_100000: Decimal = D("0.9")
    trial_quantity_factor: Decimal = D("2")
    warping_extra_loss: Decimal = D("0.0065")
    size_chemical_factor: Decimal = D("1.11")
    default_warping_loss: Decimal = D("0.10")
    hcm_small_lot_kg: Decimal = D("250")
    hcm_small_lot_factor: Decimal = D("2")
    tcdn_standard_dye_loss: Decimal = D("0.04")
    tcdn_factor_large: Decimal = D("0.95")
    tcdn_factor_dye_small: Decimal = D("1.2")
    tcdn_factor_partial_small: Decimal = D("1.5")
    min_shrinkage: Decimal = D("0.05")
    gp_threshold: Decimal = D("0.15")
    op_threshold: Decimal = D("0.064")
    yarn_price_valid_days: Decimal = D("5")

    def get(self, code: str) -> Decimal:
        return getattr(self, code)


class ParameterDefinition(BaseValueObject):
    code: str
    label: str
    unit: str = ""
    is_percent: bool = False
    so_only: bool = False
    is_ratio: bool = False  # BR-65: 0 <= x < 1
    is_threshold: bool = False  # BR-65: -100%..100%
    group: ParamGroup = ParamGroup.PRICE
    legacy: bool = False  # replaced by the 4.6.1 / 4.6.2 tables on 2026-11-25 (kept to read older sets / overrides)


def _p(code: str, label: str, unit: str = "", *, group: ParamGroup, pct: bool = False, so: bool = False,
       ratio: bool = False, thr: bool = False, legacy: bool = False) -> ParameterDefinition:  # fmt: skip
    return ParameterDefinition(
        code=code, label=label, unit=unit, is_percent=pct, so_only=so, is_ratio=ratio, is_threshold=thr, group=group,
        legacy=legacy,
    )  # fmt: skip


Y, W, H, T, P = ParamGroup.YARN, ParamGroup.WEAVING, ParamGroup.HCM, ParamGroup.TCDN, ParamGroup.PRICE

# 4.6 single values shown on Screen 5 and block G, grouped by department (2026-11-25).
PARAMETER_DEFINITIONS: Final = (
    _p("warp_loss_base", "Tiêu hao sợi dọc cơ bản", "%", group=Y, pct=True, ratio=True),
    _p("warp_loss_twist", "Tiêu hao cộng thêm khi sợi dọc có Se", "%", group=Y, pct=True, ratio=True),
    _p("warp_loss_size", "Tiêu hao cộng thêm khi sợi dọc có Hồ", "%", group=Y, pct=True, ratio=True),
    _p("weft_loss_twist_130", "Tiêu hao sợi ngang có Se @ khổ 130 cm", "%", group=Y, pct=True, ratio=True),
    _p("weft_loss_twist_175", "Tiêu hao sợi ngang có Se @ khổ 175 cm", "%", group=Y, pct=True, ratio=True),
    _p("weft_loss_twist_215", "Tiêu hao sợi ngang có Se @ khổ 215 cm", "%", group=Y, pct=True, ratio=True),
    _p("weft_loss_plain_130", "Tiêu hao sợi ngang không Se @ khổ 130 cm", "%", group=Y, pct=True, ratio=True),
    _p("weft_loss_plain_175", "Tiêu hao sợi ngang không Se @ khổ 175 cm", "%", group=Y, pct=True, ratio=True),
    _p("weft_loss_plain_215", "Tiêu hao sợi ngang không Se @ khổ 215 cm", "%", group=Y, pct=True, ratio=True),
    _p("twist_loss_offset", "Trừ khi tính sản lượng Se", "%", group=Y, pct=True, ratio=True),
    _p("yarn_waste_price", "Giá thanh lý sợi cặn", "đ/kg", group=Y),
    _p("yarn_price_valid_days", "Số ngày làm việc giá sợi còn hiệu lực", "ngày", group=Y, so=True),
    _p("warping_extra_loss", "Hao mắc cộng thêm", "%", group=W, pct=True, ratio=True),
    _p("default_warping_loss", "Độ co mắc mặc định cho mã mới", "%", group=W, pct=True, ratio=True),
    _p("size_chemical_factor", "Hệ số nhân hóa chất hồ", group=W),
    _p("tcdn_standard_dye_loss", "Tiêu hao nhuộm tiêu chuẩn TCDN", "%", group=T, pct=True, ratio=True),
    _p("sa_rate", "Tỷ lệ S&A trên giá vốn", "%", group=P, pct=True, ratio=True),
    _p("vat_rate", "VAT", "%", group=P, pct=True, ratio=True),
    _p("gp_threshold", "Ngưỡng cảnh báo GP%", "%", group=P, pct=True, so=True, thr=True),
    _p("op_threshold", "Ngưỡng cảnh báo OP%", "%", group=P, pct=True, so=True, thr=True),
    _p("bc_fabric_price", "Giá thanh lý TP B, C", "đ/m", group=P),
    _p("min_shrinkage", "Độ co tối thiểu không cần lý do", "%", group=P, pct=True, so=True, ratio=True),
)

# Values replaced by the tables 4.6.1 / 4.6.2 (2026-11-25): still read from sets stored before (they build the
# equivalent tables) and from overrides stored on older costsheets; no longer shown or typed.
LEGACY_DEFINITIONS: Final = (
    _p("greige_bc_rate_grey", "% B/C mộc khi bán Mộc", "%", group=P, pct=True, ratio=True, legacy=True),
    _p("greige_bc_rate_other", "% B/C mộc khi bán thành phẩm", "%", group=P, pct=True, ratio=True, legacy=True),
    _p("finished_bc_rate_grey", "% B/C TP khi bán Mộc", "%", group=P, pct=True, ratio=True, legacy=True),
    _p("finished_bc_rate_other", "% B/C TP khi bán thành phẩm", "%", group=P, pct=True, ratio=True, legacy=True),
    _p("qf_below_5000", "Hệ số số lượng: dưới 5.000 m mộc", group=W, legacy=True),
    _p("qf_at_5000", "Hệ số số lượng: 5.000 m mộc", group=W, legacy=True),
    _p("qf_10000_20000", "Hệ số số lượng: 10.000 - 20.000 m mộc", group=W, legacy=True),
    _p("qf_after_20000", "Hệ số số lượng: ngay sau 20.000 m mộc", group=W, legacy=True),
    _p("qf_at_50000", "Hệ số số lượng: 50.000 m mộc", group=W, legacy=True),
    _p("qf_from_100000", "Hệ số số lượng: từ 100.000 m mộc", group=W, legacy=True),
    _p("trial_quantity_factor", "Hệ số số lượng đơn Thí nghiệm", group=W, legacy=True),
    _p("hcm_small_lot_kg", "Nhuộm HCM: lô nhỏ dưới", "kg", group=H, legacy=True),
    _p("hcm_small_lot_factor", "Nhuộm HCM: hệ số thí nghiệm / lô nhỏ", group=H, legacy=True),
    _p("tcdn_factor_large", "Hệ số TCDN khi ≥ 50.000 m", group=T, legacy=True),
    _p("tcdn_factor_dye_small", "Hệ số TCDN nhuộm khi ≤ 150 m", group=T, legacy=True),
    _p("tcdn_factor_partial_small", "Hệ số TCDN partial khi ≤ 100 m", group=T, legacy=True),
)
ALL_DEFINITIONS: Final = PARAMETER_DEFINITIONS + LEGACY_DEFINITIONS

# BR-46 (2026-11-25): values sales override on one costsheet that are not single values of the set
APPLIED_WEAVING: Final = "discount_weaving"
APPLIED_HCM: Final = "discount_hcm"
APPLIED_TCDN: Final = "discount_tcdn"
APPLIED_GREIGE_BC: Final = "greige_bc_rate"
APPLIED_FINISHED_BC: Final = "finished_bc_rate"
APPLIED_CODES: Final = (APPLIED_WEAVING, APPLIED_HCM, APPLIED_TCDN, APPLIED_GREIGE_BC, APPLIED_FINISHED_BC)


class ParameterSet(BaseEntity):
    """4.6 one parameter set (never changed once saved: a new date = a new set)."""

    effective_from: date
    values: ParameterValues = Field(default_factory=ParameterValues)
    tables: ParameterTables | None = None  # None = set stored before 2026-11-25 (tables built from the values)
    created_by: str = ""

    def effective_tables(self) -> ParameterTables:
        return self.tables if self.tables is not None else legacy_tables(self.values)


class ParameterOverride(BaseValueObject):
    """4.18 a parameter changed on one costsheet."""

    parameter: str
    default_value: Decimal
    used_value: Decimal


def legacy_tables(p: ParameterValues) -> ParameterTables:
    """4.6.1 / 4.6.2 tables equal to the single values of a set stored before 2026-11-25: Dệt rows interpolated as
    the Excel formula of BR-23, HCM / TCDN rows and % B/C rows from the old values (same numbers as before)."""
    w, h, t = DiscountDepartment.WEAVING, DiscountDepartment.HCM, DiscountDepartment.TCDN
    mass, trial = DiscountCondition.MASS, DiscountCondition.TRIAL
    dyeing, partial = DiscountCondition.DYEING, DiscountCondition.PARTIAL
    rows = [
        DiscountRow(department=w, condition=mass, to_qty=QF_5000, factor=p.qf_below_5000),
        DiscountRow(department=w, condition=mass, from_qty=QF_5000, to_qty=QF_10000, factor=p.qf_at_5000,
                    interpolate=True),
        DiscountRow(department=w, condition=mass, from_qty=QF_10000, to_qty=QF_20000, to_inclusive=True,
                    factor=p.qf_10000_20000),
        DiscountRow(department=w, condition=mass, from_qty=QF_20000, from_inclusive=False, to_qty=QF_50000,
                    factor=p.qf_after_20000, interpolate=True),
        DiscountRow(department=w, condition=mass, from_qty=QF_50000, to_qty=QF_100000, factor=p.qf_at_50000,
                    interpolate=True),
        DiscountRow(department=w, condition=mass, from_qty=QF_100000, factor=p.qf_from_100000),
        DiscountRow(department=w, condition=trial, factor=p.trial_quantity_factor),
        DiscountRow(department=h, condition=trial, factor=p.hcm_small_lot_factor),
        DiscountRow(department=h, condition=mass, to_qty=p.hcm_small_lot_kg, factor=p.hcm_small_lot_factor),
        DiscountRow(department=h, condition=mass, from_qty=p.hcm_small_lot_kg, factor=D(1)),
        DiscountRow(department=t, condition=mass, from_qty=TCDN_LARGE_METERS, factor=p.tcdn_factor_large),
        DiscountRow(department=t, condition=dyeing, to_qty=TCDN_DYE_SMALL_METERS, to_inclusive=True,
                    factor=p.tcdn_factor_dye_small),
        DiscountRow(department=t, condition=dyeing, from_qty=TCDN_DYE_SMALL_METERS, from_inclusive=False,
                    factor=D(1)),
        DiscountRow(department=t, condition=partial, to_qty=TCDN_PARTIAL_SMALL_METERS, to_inclusive=True,
                    factor=p.tcdn_factor_partial_small),
        DiscountRow(department=t, condition=partial, from_qty=TCDN_PARTIAL_SMALL_METERS, from_inclusive=False,
                    factor=D(1)),
    ]  # fmt: skip
    bc = [
        BcRow(sale_form=SaleForm.GREIGE, greige_bc_rate=p.greige_bc_rate_grey,
              finished_bc_rate=p.finished_bc_rate_grey),
        BcRow(sale_form=SaleForm.FINISHED, greige_bc_rate=p.greige_bc_rate_other,
              finished_bc_rate=p.finished_bc_rate_other),
        BcRow(sale_form=SaleForm.DYED, greige_bc_rate=p.greige_bc_rate_other,
              finished_bc_rate=p.finished_bc_rate_other),
    ]  # fmt: skip
    return ParameterTables(discount_rows=rows, bc_rows=bc)


def initial_parameter_set() -> ParameterSet:
    """Initial parameter set (values of 4.6), effective 2026-01-01; tables of the Excel file (Dệt interpolated)."""
    values = ParameterValues()
    return ParameterSet(
        effective_from=date(2026, 1, 1), values=values, tables=legacy_tables(values), created_by="Hệ thống"
    )


NEW_TABLES_DATE: Final = date(2026, 11, 25)


def company_rule_set(base: ParameterSet) -> ParameterSet:
    """4.6 (2026-11-25): set effective 25/11/2026 = every value of the latest set before it, Dệt discount rows of
    the company rule (steps), liquidation prices of sợi cặn and TP B/C = 0."""
    old = base.effective_tables()
    rows = company_weaving_rows(base.values.trial_quantity_factor) + [
        r for r in old.discount_rows if r.department != DiscountDepartment.WEAVING
    ]
    values = base.values.model_copy(update={"yarn_waste_price": D(0), "bc_fabric_price": D(0)})
    return ParameterSet(
        effective_from=NEW_TABLES_DATE,
        values=values,
        tables=ParameterTables(discount_rows=rows, bc_rows=list(old.bc_rows), op_rates=list(old.op_rates)),
        created_by="Hệ thống",
    )

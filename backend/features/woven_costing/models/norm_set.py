"""4.5 Bộ định mức (12 tables + 4.5.13 spandex) and the initial set built from the Excel values (seed_norms)."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.seed_norms import (
    SEED_HCM_FEATURES,
    SEED_HCM_STAGES,
    SEED_HCM_STANDARD,
    SEED_LISTS,
    SEED_MINUTE_RATES,
    SEED_SIZE_NORMS,
    SEED_TCDN_CHEMICALS,
    SEED_TCDN_PROCESSES,
    SEED_TWIST_LEVELS,
    SEED_TWIST_PARAMS,
    SEED_WEAVE_NORMS,
    SEED_YARN_COUNTS,
)

ZERO = Decimal(0)
SEED_DATE = date(2026, 1, 1)
SEED_TWIST_STAFF = Decimal(33)
SEED_TWIST_HOURS = Decimal("22.5")
SEED_WARP = (Decimal(7800), Decimal(12), Decimal("1.97"), Decimal(11), Decimal(11))
# 4.5.13 initial values (sheet "Dữ liệu" of the Excel file): SP 40 = 16, SP 70 = 22
SEED_SPANDEX = (("40", "16"), ("70", "22"))


class MinuteRate(BaseValueObject):
    """4.5.1 one machine stage: speed, spindles, reel, minutes/day, cost per minute of the 6 items."""

    stage: str
    speed: Decimal = ZERO
    spindles: Decimal = ZERO
    reel: Decimal = ZERO
    minutes: Decimal = ZERO
    rates: CostItems = Field(default_factory=CostItems)


class TwistSystemParams(BaseValueObject):
    """4.5.2 one column (Filament / Xơ ngắn)."""

    run_rate: Decimal = ZERO
    prep_rate: Decimal = ZERO
    prep_output: Decimal = ZERO
    prep_minutes: Decimal = ZERO
    spindles: Decimal = ZERO
    machines: Decimal = ZERO
    shifts: Decimal = ZERO


class TwistParams(BaseValueObject):
    filament: TwistSystemParams = Field(default_factory=TwistSystemParams)
    spun: TwistSystemParams = Field(default_factory=TwistSystemParams)
    staff_total: Decimal = ZERO
    hours_per_day: Decimal = ZERO


class WarpCheckParams(BaseValueObject):
    """4.5.3 Mắc / Kiểm."""

    standard_ends: Decimal = ZERO
    standard_beats: Decimal = ZERO
    twist_factor: Decimal = ZERO
    check_speed_greige: Decimal = ZERO
    check_speed_dye: Decimal = ZERO


class SizeNorm(BaseValueObject):
    material: str
    group: str
    items: CostItems = Field(default_factory=CostItems)


class WeaveNorm(BaseValueObject):
    density: int
    items: CostItems = Field(default_factory=CostItems)


class YarnCount(BaseValueObject):
    fiber_system: str
    count: str
    converted: Decimal = ZERO


class HcmStandardNorm(BaseValueObject):
    fabric_type: str
    color: str
    items: CostItems = Field(default_factory=CostItems)


class HcmStageNorm(BaseValueObject):
    name: str
    items: CostItems = Field(default_factory=CostItems)
    loss_rate: Decimal = ZERO


class HcmFeatureNorm(BaseValueObject):
    feature: str
    fabric_type: str = ""
    chemical_note: str = ""
    items: CostItems = Field(default_factory=CostItems)


class TcdnProcess(BaseValueObject):
    code: str
    component: str = ""
    material: str = ""
    color: str = ""
    process: str = ""
    items: CostItems = Field(default_factory=CostItems)
    workshop: str = ""
    loss_rate: Decimal = ZERO


class TcdnChemical(BaseValueObject):
    key: str
    weight_group: str = ""
    cost: Decimal = ZERO


class ListItem(BaseValueObject):
    category: str
    value: str


class SpandexAddition(BaseValueObject):
    """4.5.13 one spandex type (number after "SP") and what it adds to the converted count (BR-81, BR-84)."""

    spandex: Decimal
    addition: Decimal = ZERO


def seed_spandex() -> list[SpandexAddition]:
    """4.5.13 initial table; also the value of norm sets stored before the table existed."""
    return [SpandexAddition(spandex=Decimal(t), addition=Decimal(a)) for t, a in SEED_SPANDEX]


class NormTables(BaseValueObject):
    """The 12 tables of one norm set (F-05 sheets) and the optional spandex table (sheet `Spandex`)."""

    minute_rates: list[MinuteRate] = Field(default_factory=list)
    twist: TwistParams = Field(default_factory=TwistParams)
    warp_check: WarpCheckParams = Field(default_factory=WarpCheckParams)
    size_norms: list[SizeNorm] = Field(default_factory=list)
    weave_norms: list[WeaveNorm] = Field(default_factory=list)
    yarn_counts: list[YarnCount] = Field(default_factory=list)
    twist_levels: list[int] = Field(default_factory=list)
    hcm_standard: list[HcmStandardNorm] = Field(default_factory=list)
    hcm_stages: list[HcmStageNorm] = Field(default_factory=list)
    hcm_features: list[HcmFeatureNorm] = Field(default_factory=list)
    tcdn_processes: list[TcdnProcess] = Field(default_factory=list)
    tcdn_chemicals: list[TcdnChemical] = Field(default_factory=list)
    lists: list[ListItem] = Field(default_factory=list)
    spandex: list[SpandexAddition] = Field(default_factory=seed_spandex)


class NormSet(BaseEntity):
    """4.5 one uploaded norm set with its effective date."""

    norm_set_code: str
    effective_from: date
    note: str = Field(default="", max_length=300)
    uploaded_by: str = ""
    tables: NormTables = Field(default_factory=NormTables)


def _d(values: tuple[str, ...]) -> list[Decimal]:
    return [Decimal(v or "0") for v in values]


def _six(values: list[Decimal]) -> CostItems:
    """NC, KH, Điện, VT, NL, CPQL."""
    return CostItems(
        labor=values[0], depreciation=values[1], power=values[2], material=values[3], fuel=values[4],
        overhead=values[5],
    )  # fmt: skip


def _hcm(values: list[Decimal]) -> CostItems:
    """HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý."""
    return CostItems(
        chemical=values[0], labor=values[1], depreciation=values[2], power=values[3], fuel=values[4],
        material=values[5], overhead=values[6],
    )  # fmt: skip


def _tcdn(values: list[Decimal]) -> CostItems:
    """Hóa chất, Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL."""
    return CostItems(
        chemical=values[0], labor=values[1], depreciation=values[2], power=values[3], fuel=values[4],
        material=values[5], overhead=values[6],
    )  # fmt: skip


def _twist_column(index: int) -> TwistSystemParams:
    values = [Decimal(row[index]) for row in SEED_TWIST_PARAMS]
    return TwistSystemParams(
        run_rate=values[0], prep_rate=values[1], prep_output=values[2], prep_minutes=values[3], spindles=values[4],
        machines=values[5], shifts=values[6],
    )  # fmt: skip


def initial_tables() -> NormTables:
    """The norm tables of the Excel files (sheets DM 2025, DM Se, DM Ho, Định mức Dệt, TỔNG HỢP, Tiêu chuẩn...)."""
    minute = []
    for row in SEED_MINUTE_RATES:
        v = _d(row[1:])
        minute.append(MinuteRate(stage=row[0], speed=v[0], spindles=v[1], reel=v[2], minutes=v[3], rates=_six(v[4:])))
    size = []
    for row in SEED_SIZE_NORMS:
        v = _d(row[2:])
        size.append(SizeNorm(material=row[0], group=row[1], items=_six(v[:6]).model_copy(update={"chemical": v[6]})))
    return NormTables(
        minute_rates=minute,
        twist=TwistParams(
            filament=_twist_column(1),
            spun=_twist_column(2),
            staff_total=SEED_TWIST_STAFF,
            hours_per_day=SEED_TWIST_HOURS,
        ),
        warp_check=WarpCheckParams(
            standard_ends=SEED_WARP[0],
            standard_beats=SEED_WARP[1],
            twist_factor=SEED_WARP[2],
            check_speed_greige=SEED_WARP[3],
            check_speed_dye=SEED_WARP[4],
        ),  # fmt: skip
        size_norms=size,
        weave_norms=[WeaveNorm(density=int(Decimal(r[0])), items=_six(_d(r[1:]))) for r in SEED_WEAVE_NORMS],
        yarn_counts=[YarnCount(fiber_system=r[0], count=r[1], converted=Decimal(r[2])) for r in SEED_YARN_COUNTS],
        twist_levels=[int(Decimal(r[0])) for r in SEED_TWIST_LEVELS],
        hcm_standard=[HcmStandardNorm(fabric_type=r[0], color=r[1], items=_hcm(_d(r[2:]))) for r in SEED_HCM_STANDARD],
        hcm_stages=[HcmStageNorm(name=r[0], items=_hcm(_d(r[1:8])), loss_rate=Decimal(r[8])) for r in SEED_HCM_STAGES],
        hcm_features=[
            HcmFeatureNorm(feature=r[0], fabric_type=r[1], chemical_note=r[2], items=_hcm(_d(r[3:])))
            for r in SEED_HCM_FEATURES
        ],
        tcdn_processes=[
            TcdnProcess(
                code=r[0],
                component=r[1],
                material=r[2],
                color=r[3],
                process=r[4],
                items=_tcdn(_d(r[5:12])),
                workshop=r[12],
                loss_rate=Decimal(r[13] or "0"),
            )  # fmt: skip
            for r in SEED_TCDN_PROCESSES
        ],
        tcdn_chemicals=[TcdnChemical(key=r[0], weight_group=r[1], cost=Decimal(r[2])) for r in SEED_TCDN_CHEMICALS],
        lists=[ListItem(category=r[0], value=r[1]) for r in SEED_LISTS],
    )


def initial_norm_set() -> NormSet:
    """Initial norm set, effective 2026-01-01, created when the table is empty."""
    return NormSet(
        norm_set_code="DM-20260101-01",
        effective_from=SEED_DATE,
        note="Định mức ban đầu (số của file Excel 2026 07 01)",
        uploaded_by="Hệ thống",
        tables=initial_tables(),
    )

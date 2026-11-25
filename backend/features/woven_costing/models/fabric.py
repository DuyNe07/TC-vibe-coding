"""4.1 Mã vải, 4.2 Thành phần sợi, 4.3 Lần cập nhật dữ liệu vải."""

from datetime import date
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.woven_costing.models.enums import FabricSource, YarnDirection, YarnKind

DEFAULT_WARPING_LOSS = Decimal("0.10")


class FabricYarn(BaseValueObject):
    """4.2 one yarn line of a fabric (order kept as in the file)."""

    direction: YarnDirection
    seq: int = Field(ge=1, le=99)
    full_yarn_name: str = ""
    yarn_code: str = ""
    yarn_name: str = ""
    rate: Decimal = Field(default=Decimal(0), ge=0, le=100)
    yarn_kind: YarnKind | None = None
    raw_yarn_code: str = ""
    raw_yarn_name: str = ""
    raw_rate: Decimal = Field(default=Decimal(100), ge=0)
    twist_tpm: str = ""

    @property
    def ratio(self) -> Decimal:
        """BR-05 ratio of the yarn in the fabric (0..1)."""
        return self.rate * self.raw_rate / Decimal(10000)


class FabricSpecs(BaseValueObject):
    """Numeric specs of 4.1 (greige + finished) and the warping loss: also the costsheet snapshot specs."""

    greige_width_cm: Decimal | None = None
    greige_cut_width_cm: Decimal | None = None
    greige_gsm: Decimal | None = None
    greige_g_per_m: Decimal | None = None
    greige_warp_density: Decimal | None = None
    greige_weft_density: Decimal | None = None
    greige_shrink_warp: Decimal | None = None
    greige_shrink_weft: Decimal | None = None
    finished_width_cm: Decimal | None = None
    finished_cut_width_cm: Decimal | None = None
    finished_gsm: Decimal | None = None
    finished_g_per_m: Decimal | None = None
    finished_warp_density: Decimal | None = None
    finished_weft_density: Decimal | None = None
    finished_shrink_warp: Decimal | None = None
    finished_shrink_weft: Decimal | None = None
    warping_loss_rate: Decimal = Field(default=DEFAULT_WARPING_LOSS, ge=0, lt=1)


class Fabric(BaseEntity):
    """4.1 one fabric code (TCFNO) with its yarns (4.2)."""

    tcfno: str = Field(min_length=10, max_length=10)
    tcfno_raw: str = Field(default="", max_length=40)
    sy_item: str = Field(default="", max_length=30)
    fabric_name: str = Field(min_length=1, max_length=300)
    structure: str = ""
    fabric_kind: str = ""
    tcfno_status: str = ""
    created_date: date | None = None
    in_charge: str = ""
    specs: FabricSpecs = Field(default_factory=FabricSpecs)
    source: FabricSource = FabricSource.MANUAL
    remark: str = Field(default="", max_length=500)
    updated_by: str = ""
    yarns: list[FabricYarn] = Field(default_factory=list)

    @property
    def has_yarns(self) -> bool:
        return bool(self.yarns)

    @property
    def ratio_total(self) -> Decimal:
        return sum((y.ratio for y in self.yarns), Decimal(0))


class FabricImportLog(BaseEntity):
    """4.3 one saved fabric import."""

    imported_by: str
    file_names: str
    new_count: int = 0
    changed_count: int = 0
    unchanged_count: int = 0
    missing_yarn_count: int = 0
    error_count: int = 0

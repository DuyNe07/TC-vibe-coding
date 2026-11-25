"""BR-75 fabric label: finished specs of the master data, fabric name, up to 6 warp + 6 weft yarns."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.numbers import round_half_up
from backend.features.woven_costing.constants import CM_PER_INCH, MAX_LABEL_YARNS
from backend.features.woven_costing.models.enums import YarnDirection
from backend.features.woven_costing.models.fabric import Fabric
from backend.features.woven_costing.models.label import FabricLabel

HUNDRED = Decimal(100)
DIRECTION_TEXT = {YarnDirection.WARP: "Warp", YarnDirection.WEFT: "Weft"}


def _text(value: Decimal | None) -> str:
    """Empty or 0 specs are printed empty (BR-75)."""
    if not value:
        return ""
    return f"{value.normalize():f}"


class LabelBusiness(BaseBusiness[Fabric]):
    def rules(self) -> Sequence[BaseBusinessRule[Fabric]]:
        return ()

    def yarn_ratio(self, rate: Decimal, raw_rate: Decimal) -> Decimal:
        """BR-75: rate / 100 x raw_rate / 100."""
        return rate / HUNDRED * raw_rate / HUNDRED

    def build(self, fabric: Fabric, remark: str) -> FabricLabel:
        """BR-75: always the finished specs; WIDTH in cm and round(cm / 2.54) INCH."""
        specs = fabric.specs
        lines = []
        for direction in (YarnDirection.WARP, YarnDirection.WEFT):
            yarns = [y for y in fabric.yarns if y.direction == direction][:MAX_LABEL_YARNS]
            for yarn in yarns:
                ratio = self.yarn_ratio(yarn.rate, yarn.raw_rate) * HUNDRED
                lines.append(f"{DIRECTION_TEXT[direction]} {yarn.seq}: {yarn.yarn_name} {ratio:.2f}%")
        width = specs.finished_width_cm
        inch = _text(round_half_up(width / CM_PER_INCH)) if width else ""
        return FabricLabel(
            tcfno=fabric.tcfno,
            fabric_name=fabric.fabric_name,
            yarn_lines=lines,
            width_cm=_text(width),
            width_inch=inch,
            gsm=_text(specs.finished_gsm),
            g_per_m=_text(specs.finished_g_per_m),
            warp_density=_text(specs.finished_warp_density),
            weft_density=_text(specs.finished_weft_density),
            remark=remark.strip(),
        )

"""UC-27 / UC-29: yarns → rows of sheet 'Bang gia' (5.4) filtered like the screen and sorted by factory, base code,
line type."""

import re
from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.yarn_costing.constants import NO_CARDING_LABEL
from backend.features.yarn_costing.dto.price_dto import ListPriceLinesRequest, PriceLineRowDTO
from backend.features.yarn_costing.models.enums import LineType
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import PriceLine, Yarn

LINE_ORDER = {LineType.THUONG: 0, LineType.THI_NGHIEM: 1, LineType.CHIET_KHAU: 2, LineType.PHU_PHI: 3}


def percent_text(ratio: Decimal) -> str:
    """70% / 33,33% (up to 2 decimals, Vietnamese comma)."""
    value = (ratio * 100).quantize(Decimal("0.01"))
    text = f"{value:f}".rstrip("0").rstrip(".")
    return text.replace(".", ",") + "%"


def components_text(yarn: Yarn, single_pass_lines: set[tuple[str, str]]) -> str:
    """5.4 cột 'Thành phần': "Cotton 70% (C1); Viscose - Ring 30% (C3 lượt 1)"."""
    parts = []
    for c in yarn.components:
        if not c.carding_stage:
            where = NO_CARDING_LABEL
        elif (yarn.factory_code.value, c.carding_stage) in single_pass_lines:
            where = c.carding_stage
        else:
            where = f"{c.carding_stage} lượt {c.pass_no or 1}"
        parts.append(f"{c.material_label} {percent_text(c.ratio)} ({where})")
    return "; ".join(parts)


def base_sort_key(code: str) -> tuple[int, str]:
    match = re.fullmatch(r"S\d-(\d+)", code)
    return (int(match.group(1)) if match else 10**9, code)


class PriceLineRowsBuilder(BaseBuilder[list[PriceLineRowDTO]]):
    def __init__(
        self,
        yarns: list[Yarn],
        request: ListPriceLinesRequest,
        exchange_rate: Decimal | None,
        packaging_names: dict[tuple[str, str], str],
        stages: list[Stage] | None = None,
    ) -> None:
        self.yarns, self.request, self.rate, self.packaging_names = yarns, request, exchange_rate, packaging_names
        self.single_pass_lines = {
            (s.factory_code.value, s.stage_code) for s in stages or [] if s.is_carding and s.pass_limit == 1
        }

    def _yarn_ok(self, y: Yarn) -> bool:
        r = self.request
        return (
            (r.factory_code is None or y.factory_code == r.factory_code)
            and (not r.statuses or y.status in r.statuses)
            and (r.technology is None or y.technology == r.technology)
            and (not r.yarn_group or y.yarn_group == r.yarn_group.strip().upper())
            and (r.priced_from is None or (y.first_priced_at is not None and y.first_priced_at >= r.priced_from))
            and (r.priced_to is None or (y.first_priced_at is not None and y.first_priced_at <= r.priced_to))
        )

    def _line_ok(self, y: Yarn, line: PriceLine) -> bool:
        r = self.request
        keyword = r.keyword.strip().casefold()
        text = f"{line.line_code} {y.yarn_name} {line.accounting_code or ''}".casefold()
        return (
            (not r.line_types or line.line_type in r.line_types)
            and (r.has_accounting_code is None or line.has_accounting_code == r.has_accounting_code)
            and (not keyword or keyword in text)
        )

    def build(self) -> list[PriceLineRowDTO]:
        pairs = [(y, line) for y in self.yarns if self._yarn_ok(y) for line in y.lines if self._line_ok(y, line)]
        pairs.sort(
            key=lambda p: (
                p[0].factory_code.value,
                base_sort_key(p[0].base_code),
                p[0].revision_no,
                LINE_ORDER[p[1].line_type],
                p[1].line_code,
            )
        )
        rows = []
        for index, (y, line) in enumerate(pairs, start=1):
            c = line.cost
            rows.append(
                PriceLineRowDTO(
                    stt=index,
                    factory_code=y.factory_code,
                    line_code=line.line_code,
                    line_type=line.line_type,
                    base_code=y.base_code,
                    yarn_code=y.yarn_code,
                    yarn_name=y.yarn_name,
                    yarn_group=y.yarn_group,
                    count=y.count,
                    technology=y.technology,
                    loss_group_key=y.loss_group_key,
                    components_text=components_text(y, self.single_pass_lines),
                    labor=c.labor,
                    depreciation=c.depreciation,
                    electricity=c.electricity,
                    materials=c.materials,
                    overhead=c.overhead,
                    total_vnd=c.total,
                    usd_per_kg=c.total / self.rate if self.rate else None,
                    exchange_rate=self.rate,
                    packaging_code=y.packaging_code,
                    packaging_name=self.packaging_names.get((y.factory_code.value, y.packaging_code or ""), ""),
                    first_priced_at=y.first_priced_at,
                    effective_date=y.effective_date,
                    status=y.status,
                    accounting_code=line.accounting_code,
                    adjustment_percent=line.adjustment_percent,
                    adjustment_reason=line.adjustment_reason,
                    order_ref=line.order_ref,
                    is_locked=y.is_locked,
                )
            )
        return rows

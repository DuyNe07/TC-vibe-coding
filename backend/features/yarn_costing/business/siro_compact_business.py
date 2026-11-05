"""BR-71 Siro / Compact bất thường: loại sợi theo tên, kiểm tra NSM Con và giá trong (xưởng, nhóm sợi, chi số)."""

from collections import Counter, defaultdict
from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.models.analysis import SiroNsmAnomaly, SiroPriceAnomaly
from backend.features.yarn_costing.models.enums import Technology, YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn

KIND_NORMAL = "Thường"
KIND_SIRO_OR_COMPACT = "Siro / Compact"
KIND_SIRO_COMPACT = "Siro Compact"
KIND_FACTOR = {KIND_NORMAL: Decimal(1), KIND_SIRO_OR_COMPACT: Decimal("0.95"), KIND_SIRO_COMPACT: Decimal("0.90")}
KIND_RANK = {KIND_NORMAL: 0, KIND_SIRO_OR_COMPACT: 1, KIND_SIRO_COMPACT: 2}
CONVERTED_BASELINE = "Quy đổi từ sợi Siro / Compact"
NSM_TOLERANCE_PERCENT = Decimal(1)
SPIN_STAGE = "S"
SPIN_COMPACT_STAGE = "S Compact"
PRICED_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)
ZERO = Decimal(0)
HUNDRED = Decimal(100)
NSM_PLACES = Decimal("0.0001")
PERCENT_PLACES = Decimal("0.01")

GroupKey = tuple[str, str, Decimal]


class SiroCompactBusiness(BaseBusiness[Yarn]):
    def kind_of(self, yarn_name: str) -> str:
        """BR-71: 'SIRO' và 'COMPACT' → Siro Compact; một trong hai → Siro / Compact; không có → Thường."""
        name = yarn_name.upper()
        siro, compact = "SIRO" in name, "COMPACT" in name
        if siro and compact:
            return KIND_SIRO_COMPACT
        return KIND_SIRO_OR_COMPACT if siro or compact else KIND_NORMAL

    def spin_nsm(self, yarn: Yarn) -> Decimal:
        """BR-71: NSM Con = NSM ở 'S Compact' nếu > 0, ngược lại NSM ở 'S'."""
        compact = yarn.nsm_at(SPIN_COMPACT_STAGE)
        return compact if compact > ZERO else yarn.nsm_at(SPIN_STAGE)

    def groups(self, yarns: Sequence[Yarn]) -> dict[GroupKey, list[Yarn]]:
        """BR-71 phạm vi: bản gốc đã có giá, Ring; gom (xưởng, nhóm sợi, chi số); nhóm có mã Siro / Compact và ≥ 2 mã."""
        grouped: dict[GroupKey, list[Yarn]] = defaultdict(list)
        for y in yarns:
            if y.is_base and y.status in PRICED_STATUSES and y.technology == Technology.RING and y.count is not None:
                grouped[(y.factory_code.value, y.yarn_group, y.count)].append(y)
        return {
            key: sorted(members, key=lambda y: y.yarn_code)
            for key, members in sorted(grouped.items())
            if len(members) >= 2 and any(self.kind_of(y.yarn_name) != KIND_NORMAL for y in members)
        }

    @staticmethod
    def _common(values: Sequence[Decimal]) -> Decimal:
        """Giá trị phổ biến (xuất hiện nhiều nhất; bằng nhau: nhỏ nhất)."""
        counts = Counter(values)
        return min(counts, key=lambda v: (-counts[v], v))

    def nsm_anomalies(self, yarns: Sequence[Yarn]) -> list[SiroNsmAnomaly]:
        """BR-71 (1): NSM chuẩn = mốc thường × hệ số; |lệch| > 1% → liệt kê."""
        result: list[SiroNsmAnomaly] = []
        for (factory, yarn_group, count), members in self.groups(yarns).items():
            rows = [(y, self.kind_of(y.yarn_name), self.spin_nsm(y)) for y in members]
            rows = [r for r in rows if r[2] > ZERO]
            normal = [r for r in rows if r[1] == KIND_NORMAL]
            if normal:
                baseline = self._common([nsm for _, _, nsm in normal])
                baseline_code = next(y.yarn_code for y, _, nsm in normal if nsm == baseline)
            else:
                lowest = min((KIND_RANK[kind] for _, kind, _ in rows), default=None)
                pool = [nsm / KIND_FACTOR[kind] for _, kind, nsm in rows if KIND_RANK[kind] == lowest]
                if not pool:
                    continue
                baseline, baseline_code = self._common(pool), CONVERTED_BASELINE
            for y, kind, nsm in rows:
                if kind == KIND_NORMAL:
                    continue
                standard = baseline * KIND_FACTOR[kind]
                diff = (nsm - standard) / standard * HUNDRED
                if abs(diff) > NSM_TOLERANCE_PERCENT:
                    result.append(
                        SiroNsmAnomaly(
                            factory_code=factory,
                            yarn_group=yarn_group,
                            count=count,
                            yarn_code=y.yarn_code,
                            yarn_name=y.yarn_name,
                            kind=kind,
                            nsm=nsm,
                            standard_nsm=standard.quantize(NSM_PLACES, rounding=ROUND_HALF_UP),
                            diff_percent=diff.quantize(PERCENT_PLACES, rounding=ROUND_HALF_UP),
                            baseline=baseline_code,
                        )
                    )
        return result

    def price_anomalies(self, yarns: Sequence[Yarn]) -> list[SiroPriceAnomaly]:
        """BR-71 (2): mã hạng trên Thường phải đắt hơn mã đắt nhất của các hạng thấp hơn cùng nhóm."""
        result: list[SiroPriceAnomaly] = []
        for (factory, yarn_group, count), members in self.groups(yarns).items():
            priced = [(y, self.kind_of(y.yarn_name), y.regular_line) for y in members if y.regular_line is not None]
            for y, kind, line in priced:
                rank = KIND_RANK[kind]
                lower = [(o, k, ol) for o, k, ol in priced if KIND_RANK[k] < rank]
                if not lower:
                    continue
                other, other_kind, other_line = min(lower, key=lambda r: (-r[2].total_vnd, r[0].yarn_code))
                if line.total_vnd <= other_line.total_vnd:  # type: ignore[union-attr]
                    result.append(
                        SiroPriceAnomaly(
                            factory_code=factory,
                            yarn_group=yarn_group,
                            count=count,
                            yarn_code=y.yarn_code,
                            yarn_name=y.yarn_name,
                            kind=kind,
                            total=line.total_vnd,  # type: ignore[union-attr]
                            compare_code=other.yarn_code,
                            compare_kind=other_kind,
                            compare_total=other_line.total_vnd,
                            reason=f"Sợi {kind} nhưng giá không cao hơn sợi {other_kind}",
                        )
                    )
        return result

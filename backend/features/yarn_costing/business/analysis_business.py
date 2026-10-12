"""Sợi so sánh BR-37, cảnh báo NSM BR-38, giá bất thường BR-39, NSM bất thường BR-54, đối chiếu giá cũ BR-55."""

from collections import Counter, defaultdict
from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.constants import MATCH_TOLERANCE_VND
from backend.features.yarn_costing.models.analysis import LegacyComparison, NsmAnomaly, PriceAnomaly
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.models.stage import Stage
from backend.features.yarn_costing.models.yarn import Yarn, YarnComponent
from backend.shared.utils import normalize_key

PRICED_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)
SAME_COUNT_REASON = "Cùng chi số nhưng khác giá"
HIGHER_COUNT_REASON = "Chi số cao hơn nhưng giá không cao hơn"
ZERO = Decimal(0)


class AnalysisBusiness(BaseBusiness[Yarn]):
    def reference_yarn(self, target: Yarn, yarns: Sequence[Yarn]) -> Yarn | None:
        """BR-37: cùng xưởng, khác X, Đã tính giá / Có mã kế toán, cùng công nghệ; ưu tiên cùng nhóm tiêu hao,
        rồi cùng nhóm sợi; chọn chi số gần nhất (bằng nhau: mã tính giá lần cuối gần nhất)."""
        candidates = [
            y
            for y in yarns
            if y.factory_code == target.factory_code
            and y.yarn_code != target.yarn_code
            and y.status in PRICED_STATUSES
            and y.technology == target.technology
        ]
        pool = [y for y in candidates if y.loss_group_key == target.loss_group_key] or [
            y for y in candidates if y.yarn_group and y.yarn_group == target.yarn_group
        ]
        if not pool:
            return None
        count = target.count or ZERO

        def key(y: Yarn) -> tuple[Decimal, float]:
            stamp = y.last_calculated_at.timestamp() if y.last_calculated_at else 0.0
            return (abs((y.count or ZERO) - count), -stamp)

        return min(pool, key=key)

    def carding_nsm(self, yarn: Yarn) -> dict[tuple[str, str], tuple[str, Decimal]]:
        """BR-37 / BR-38 / BR-54: NSM chải thô theo cặp (dây chuyền, nguyên liệu) → (tên hiển thị, NSM)."""
        return {
            (c.carding_stage, normalize_key(c.material_label)): (f"{c.carding_stage} ({c.material_label})", c.nsm_value)
            for c in yarn.components
            if c.carding_stage
        }

    def pair_key(self, component: YarnComponent) -> tuple[str, str] | None:
        """(dây chuyền, nguyên liệu) of a carding component (None = Không chải thô)."""
        return (component.carding_stage, normalize_key(component.material_label)) if component.carding_stage else None

    def warning_stages(self, target: Yarn, reference: Yarn | None, stages: Sequence[Stage]) -> list[str]:
        """BR-38: công đoạn varies_with_count = Không (trừ F) mà NSM khác sợi so sánh; dây chuyền chải thô so theo cặp
        dây chuyền + nguyên liệu."""
        if reference is None:
            return []
        result: list[str] = []
        mine, theirs = self.carding_nsm(target), self.carding_nsm(reference)
        for s in sorted(stages, key=lambda s: s.sequence):
            if s.varies_with_count or s.is_packaging:
                continue
            if s.is_carding:
                keys = [k for k in dict.fromkeys([*mine, *theirs]) if k[0] == s.stage_code]
                for key in keys:
                    label = (mine.get(key) or theirs[key])[0]
                    if mine.get(key, (label, ZERO))[1] != theirs.get(key, (label, ZERO))[1]:
                        result.append(label)
            elif target.nsm_at(s.stage_code) != reference.nsm_at(s.stage_code):
                result.append(s.stage_code)
        return result

    def price_anomalies(self, yarns: Sequence[Yarn]) -> list[PriceAnomaly]:
        """BR-39: dòng Thường của bản GỐC đã có giá, gom theo (xưởng, công nghệ, nhóm sợi, nhóm tiêu hao), sắp theo chi số;
        cặp liền nhau: cùng chi số khác giá (> 1 VND/kg) hoặc chi số cao hơn mà giá không cao hơn."""
        groups: dict[tuple[str, str, str, str], list[Yarn]] = defaultdict(list)
        for y in yarns:
            if y.is_base and y.status in PRICED_STATUSES and y.regular_line is not None:
                groups[(y.factory_code.value, y.technology.value, y.yarn_group, y.loss_group_key)].append(y)
        result: list[PriceAnomaly] = []
        for (factory, tech, yarn_group, loss_key), members in sorted(groups.items()):
            members.sort(key=lambda y: (y.count or ZERO, y.yarn_code))
            for prev, nxt in zip(members, members[1:], strict=False):
                prev_total = prev.regular_line.total_vnd  # type: ignore[union-attr]
                next_total = nxt.regular_line.total_vnd  # type: ignore[union-attr]
                reason = ""
                if (prev.count or ZERO) == (nxt.count or ZERO) and abs(next_total - prev_total) > MATCH_TOLERANCE_VND:
                    reason = SAME_COUNT_REASON
                elif (nxt.count or ZERO) > (prev.count or ZERO) and next_total <= prev_total:
                    reason = HIGHER_COUNT_REASON
                if reason:
                    result.append(
                        PriceAnomaly(
                            factory_code=factory,
                            technology=tech,
                            yarn_group=yarn_group,
                            loss_group_key=loss_key,
                            prev_code=prev.yarn_code,
                            prev_count=prev.count,
                            prev_total=prev_total,
                            next_code=nxt.yarn_code,
                            next_count=nxt.count,
                            next_total=next_total,
                            reason=reason,
                        )
                    )
        return result

    def nsm_anomalies(self, yarns: Sequence[Yarn], stages_by_factory: dict[str, list[Stage]]) -> list[NsmAnomaly]:
        """BR-54: gom bản NSM đã có giá theo (xưởng, công nghệ, nhóm tiêu hao), nhóm ≥ 2 mã; mỗi công đoạn
        varies_with_count = Không: giá trị phổ biến (bằng nhau: nhỏ nhất); liệt kê mã có NSM khác."""
        groups: dict[tuple[str, str, str], list[Yarn]] = defaultdict(list)
        for y in yarns:
            if y.status in PRICED_STATUSES:
                groups[(y.factory_code.value, y.technology.value, y.loss_group_key)].append(y)
        result: list[NsmAnomaly] = []
        for (factory, tech, loss_key), members in sorted(groups.items()):
            if len(members) < 2:
                continue
            for stage in sorted(stages_by_factory.get(factory, []), key=lambda s: s.sequence):
                if stage.varies_with_count or stage.is_packaging:
                    continue
                if stage.is_carding:
                    series: dict[tuple[str, str], list[tuple[Yarn, str, Decimal]]] = defaultdict(list)
                    for y in members:
                        for key, (label, value) in self.carding_nsm(y).items():
                            if key[0] == stage.stage_code:
                                series[key].append((y, label, value))
                    for key in sorted(series):
                        rows = series[key]
                        if len(rows) < 2:
                            continue
                        result += self._anomalies(factory, tech, loss_key, rows[0][1], [(y, v) for y, _, v in rows])
                    continue
                result += self._anomalies(
                    factory, tech, loss_key, stage.stage_code, [(y, y.nsm_at(stage.stage_code)) for y in members]
                )
        return result

    def _anomalies(
        self, factory: str, tech: str, loss_key: str, stage_label: str, values: list[tuple[Yarn, Decimal]]
    ) -> list[NsmAnomaly]:
        """BR-54: giá trị phổ biến (bằng nhau: nhỏ nhất); mã có NSM khác được liệt kê."""
        counts = Counter(v for _, v in values)
        common = min(counts, key=lambda v: (-counts[v], v))
        return [
            NsmAnomaly(
                factory_code=factory,
                technology=tech,
                loss_group_key=loss_key,
                stage_code=stage_label,
                common_value=common,
                yarn_code=y.yarn_code,
                nsm=value,
                reason=y.nsm_warning_reason,
            )
            for y, value in sorted(values, key=lambda p: p[0].yarn_code)
            if value != common
        ]

    def compare_legacy(self, yarn_code: str, old_total: Decimal, yarn: Yarn | None) -> LegacyComparison:
        """BR-55: chênh lệch = Tổng app − Tổng cũ; khớp nếu |chênh lệch| ≤ 1 VND/kg; % = chênh lệch ÷ Tổng cũ × 100."""
        regular = yarn.regular_line if yarn is not None else None
        if yarn is None or regular is None or yarn.status == YarnStatus.CHUA_TINH_DUOC:
            return LegacyComparison(
                yarn_code=yarn_code,
                yarn_name=yarn.yarn_name if yarn else "",
                old_total=old_total,
                status=yarn.status.value if yarn else "Không có dữ liệu NSM",
            )
        diff = regular.total_vnd - old_total
        return LegacyComparison(
            yarn_code=yarn_code,
            yarn_name=yarn.yarn_name,
            old_total=old_total,
            app_total=regular.total_vnd,
            diff_vnd=diff,
            diff_percent=diff / old_total * 100 if old_total != 0 else None,
            matched=abs(diff) <= MATCH_TOLERANCE_VND,
            status=yarn.status.value,
        )

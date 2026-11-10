"""UC-52 So sánh 2 sợi (bổ sung 2026-11-10): two price lines side by side. Không lưu gì."""

from datetime import date
from decimal import Decimal

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import usd
from backend.features.yarn_costing.builders.price_rows_builder import components_text, percent_text
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.customer_name_business import CustomerNameBusiness
from backend.features.yarn_costing.dto.sales_dto import (
    CompareInfoRowDTO,
    ComparePriceLinesRequest,
    ComparePriceLinesResponse,
    ComparePriceRowDTO,
    CompareStageRowDTO,
)
from backend.features.yarn_costing.exceptions import YarnNotFoundError, YarnValidationError
from backend.features.yarn_costing.models.yarn import PriceLine, StageCostDetail, Yarn
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

MSG_SAME = "Hãy chọn hai dòng giá khác nhau."
HUNDRED = Decimal(100)


def stage_key(detail: StageCostDetail) -> tuple[str, str]:
    """Carding lines are compared per material and pass, other stages per stage code."""
    if detail.material_label:
        return detail.stage_code, f"{detail.stage_code} ({detail.material_label} lượt {detail.pass_no or 1})"
    return detail.stage_code, detail.stage_code


class ComparePriceLinesService(BaseService[ComparePriceLinesRequest, ComparePriceLinesResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()

    def _find(self, yarns: list[Yarn], code: str) -> tuple[Yarn, PriceLine]:
        for yarn in yarns:
            line = yarn.line(code)
            if line is not None:
                return yarn, line
        raise YarnNotFoundError(f"Không tìm thấy dòng giá {code}.")

    def execute(self, request: ComparePriceLinesRequest) -> ComparePriceLinesResponse:
        if request.line_a == request.line_b:
            raise YarnValidationError(MSG_SAME)
        yarns = self.repository.list_all()
        (ya, la), (yb, lb) = self._find(yarns, request.line_a), self._find(yarns, request.line_b)
        aliases = CustomerNameBusiness()
        by_base = aliases.by_base(CustomerYarnNameRepository().list_all())
        stages = StageRepository().list_all()
        single = {(s.factory_code.value, s.stage_code) for s in stages if s.is_carding and s.pass_limit == 1}
        packaging = {(p.factory_code.value, p.code): p.name for p in PackagingTypeRepository().list_all()}

        def info(y: Yarn, line: PriceLine) -> list[str]:
            pack = packaging.get((y.factory_code.value, y.packaging_code or ""), "")
            return [
                y.factory_code.value,
                line.line_code,
                line.line_type.value,
                y.yarn_name,
                aliases.text(by_base.get(y.base_code, [])),
                y.yarn_group,
                f"{y.count.normalize():f}" if y.count is not None else "",
                y.technology.value,
                y.loss_group_key,
                components_text(y, single),
                f"{y.packaging_code or ''} {pack}".strip(),
                y.status.value,
                line.accounting_code or "",
                percent_text(line.adjustment_percent) if line.adjustment_percent is not None else "",
            ]

        labels = [
            "Xưởng",
            "Mã dòng",
            "Loại dòng",
            "Tên chuẩn",
            "Tên theo khách",
            "Nhóm sợi",
            "Chi số",
            "Công nghệ",
            "Nhóm tiêu hao",
            "Thành phần",
            "Loại đóng gói",
            "Trạng thái",
            "Mã kế toán",
            "% CK/PP",
        ]
        info_rows = [
            CompareInfoRowDTO(label=label, a=a, b=b)
            for label, a, b in zip(labels, info(ya, la), info(yb, lb), strict=True)
        ]
        rate = CostingBusiness().current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        ca, cb = la.cost, lb.cost
        values = [
            ("Nhân công", ca.labor, cb.labor),
            ("Khấu hao", ca.depreciation, cb.depreciation),
            ("Điện", ca.electricity, cb.electricity),
            ("Vật tư", ca.materials, cb.materials),
            ("CPQL", ca.overhead, cb.overhead),
            ("Tổng (VND/kg)", ca.total, cb.total),
        ]
        rate_value = rate.rate if rate else None
        values.append(("USD/kg", usd(ca.total, rate_value), usd(cb.total, rate_value)))  # type: ignore[arg-type]
        prices = [
            ComparePriceRowDTO(
                label=label,
                a=a,
                b=b,
                difference=b - a if a is not None and b is not None else None,
                difference_percent=(b - a) / a * HUNDRED if a and b is not None else None,
            )
            for label, a, b in values
        ]
        return ComparePriceLinesResponse(info=info_rows, prices=prices, stages=self._stages(ya, la, yb, lb, stages))

    def _scaled(self, yarn: Yarn, line: PriceLine) -> Decimal:
        """Stage costs are those of the Thường line: scale them so they add up to the chosen line."""
        regular = yarn.regular_line
        return line.total_vnd / regular.total_vnd if regular and regular.total_vnd else Decimal(1)

    def _stages(self, ya: Yarn, la: PriceLine, yb: Yarn, lb: PriceLine, stages: list) -> list[CompareStageRowDTO]:
        sequence = {s.stage_code: s.sequence for s in stages}
        names = {s.stage_code: s.stage_name for s in stages}
        rows: dict[str, CompareStageRowDTO] = {}
        order: dict[str, tuple[int, str]] = {}
        for side, yarn, line in (("a", ya, la), ("b", yb, lb)):
            factor = self._scaled(yarn, line)
            for d in yarn.stage_details:
                code, label = stage_key(d)
                row = rows.setdefault(
                    label, CompareStageRowDTO(stage_code=label, stage_name=d.stage_name or names.get(code, ""))
                )
                order[label] = (d.sequence or sequence.get(code, 999), label)
                rows[label] = row.model_copy(
                    update={f"nsm_{side}": d.nsm, f"loss_{side}": d.loss, f"cost_{side}": d.cost_per_kg * factor}
                )
        return [rows[k] for k in sorted(rows, key=lambda k: order[k])]

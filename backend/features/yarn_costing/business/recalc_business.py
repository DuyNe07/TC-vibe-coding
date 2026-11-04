"""BR-36 tính lại toàn bộ một xưởng, BR-40 tính lại mã chờ tiêu hao, BR-24 tính lại mã bị ảnh hưởng,
BR-65 tính lại các mã chưa tính được."""

from collections.abc import Callable, Sequence
from datetime import date, datetime

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.price_line_business import PriceLineBusiness
from backend.features.yarn_costing.models.costing import FactoryData, RecalcOutcome
from backend.features.yarn_costing.models.enums import FactoryCode, PriceEvent, YarnStatus
from backend.features.yarn_costing.models.recalc_batch import RecalcBatch
from backend.features.yarn_costing.models.yarn import Yarn

PROCESSED_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN, YarnStatus.CHUA_TINH_DUOC)


class RecalcBusiness(BaseBusiness[Yarn]):
    def __init__(self) -> None:
        self.costing = CostingBusiness()
        self.lines = PriceLineBusiness()

    def is_recalculable(self, yarn: Yarn) -> bool:
        return yarn.status in PROCESSED_STATUSES

    def recalculate(
        self,
        yarns: Sequence[Yarn],
        data: FactoryData,
        event: PriceEvent,
        now: datetime,
        effective_date: date,
        selector: Callable[[Yarn], bool] | None = None,
        **ctx: object,
    ) -> RecalcOutcome:
        """BR-36: mọi bản NSM Đã tính giá / Có mã kế toán / Chưa tính được của xưởng (kể cả đã khoá) được tính lại.

        Đạt → cập nhật dòng Thường, TN, CK/PP, chi tiết, ngày hiệu lực; không đạt → Chưa tính được (giữ giá cũ).
        Mỗi dòng giá có Tổng thay đổi được ghi lịch sử. ``selector`` giới hạn các bản được tính (BR-24, BR-40).
        """
        updated, history = [], []
        failed = changed = line_count = 0
        for yarn in yarns:
            if yarn.factory_code != data.factory_code or not self.is_recalculable(yarn):
                continue
            if selector is not None and not selector(yarn):
                continue
            result = self.costing.calculate(yarn, data)
            new_yarn, entries = self.lines.apply_result(
                yarn, result, data.trial_factor, event, now, effective_date, **ctx
            )
            failed += 0 if result.passed else 1
            changed += len(entries)
            line_count += len(new_yarn.lines)
            updated.append(new_yarn)
            history.extend(entries)
        return RecalcOutcome(
            yarns=updated,
            history=history,
            yarn_count=len(updated),
            failed_yarn_count=failed,
            changed_line_count=changed,
            line_count=line_count,
        )

    def recalculate_waiting(
        self, yarns: Sequence[Yarn], data: FactoryData, group_key: str, now: datetime, **ctx: object
    ) -> RecalcOutcome:
        """BR-40: nhóm tiêu hao mới → tính lại các bản 'Chưa tính được' cùng xưởng có nhóm tiêu hao = nhóm mới."""
        return self.recalculate(
            yarns,
            data,
            PriceEvent.SUA_TIEU_HAO,
            now,
            now.date(),
            selector=lambda y: y.status == YarnStatus.CHUA_TINH_DUOC and y.loss_group_key == group_key,
            **ctx,
        )

    def not_priced(self, yarns: Sequence[Yarn], factory_code: FactoryCode) -> list[Yarn]:
        """BR-65: các bản NSM của xưởng đang 'Chưa tính được' (kể cả bản đã khoá)."""
        return [y for y in yarns if y.factory_code == factory_code and y.status == YarnStatus.CHUA_TINH_DUOC]

    def recalculate_not_priced(
        self, yarns: Sequence[Yarn], data: FactoryData, now: datetime, effective_date: date, **ctx: object
    ) -> RecalcOutcome:
        """BR-65: chỉ tính lại các bản 'Chưa tính được' của xưởng, event / trigger 'Tính lại mã chưa tính được'."""
        return self.recalculate(
            yarns,
            data,
            PriceEvent.TINH_LAI_CHUA_TINH,
            now,
            effective_date,
            selector=lambda y: y.status == YarnStatus.CHUA_TINH_DUOC,
            **ctx,
        )

    def make_batch(
        self,
        factory_code: FactoryCode,
        trigger: PriceEvent,
        effective_date: date,
        reason: str,
        run_by: str,
        outcome: RecalcOutcome,
        existing_codes: Sequence[str],
    ) -> RecalcBatch:
        """BR-36: một bản ghi 4.16 cho mỗi lần tính lại toàn bộ."""
        return RecalcBatch(
            batch_code=self.batch_code(factory_code.value, existing_codes),
            factory_code=factory_code,
            trigger=trigger,
            effective_date=effective_date,
            reason=reason,
            run_by=run_by,
            yarn_count=outcome.yarn_count,
            changed_line_count=outcome.changed_line_count,
            failed_yarn_count=outcome.failed_yarn_count,
            line_count=outcome.line_count,
        )

    def batch_code(self, factory_code: str, existing_codes: Sequence[str]) -> str:
        """4.16: mã lần tính lại TL-<xưởng>-NNN."""
        prefix = f"TL-{factory_code}-"
        numbers = [int(c[len(prefix) :]) for c in existing_codes if c.startswith(prefix) and c[len(prefix) :].isdigit()]
        return f"{prefix}{max(numbers, default=0) + 1:03d}"

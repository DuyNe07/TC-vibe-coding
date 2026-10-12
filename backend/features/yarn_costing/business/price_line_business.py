"""Dòng bảng giá: BR-30 thí nghiệm, BR-31 CK/PP, BR-32 khoá + trạng thái, BR-34, BR-35; lịch sử giá (4.15)."""

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.constants import STORAGE_QUANTUM
from backend.features.yarn_costing.models.costing import AdjustmentInput, CostResult
from backend.features.yarn_costing.models.enums import LineType, PriceEvent, YarnStatus
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, StageCostDetail, Yarn

ONE = Decimal(1)
LINE_TYPE_ORDER = {LineType.THUONG: 0, LineType.THI_NGHIEM: 1, LineType.CHIET_KHAU: 2, LineType.PHU_PHI: 3}
TRIAL_SUFFIX = "TN"
ADJUSTMENT_TYPES = (LineType.CHIET_KHAU, LineType.PHU_PHI)


def stored(value: Decimal) -> Decimal:
    """Stored amounts keep 10 decimals (the display rounds to 0-4 decimals, BR-23)."""
    return value.quantize(STORAGE_QUANTUM)


def stored_cost(cost: CostBreakdown) -> CostBreakdown:
    return CostBreakdown(
        labor=stored(cost.labor),
        depreciation=stored(cost.depreciation),
        electricity=stored(cost.electricity),
        materials=stored(cost.materials),
        overhead=stored(cost.overhead),
    )


def stored_detail(detail: StageCostDetail) -> StageCostDetail:
    return detail.model_copy(
        update={
            "run_minutes": stored(detail.run_minutes),
            "cumulative_loss": stored(detail.cumulative_loss),
            "cost": stored_cost(detail.cost),
        }
    )


class AdjustmentLineRule(BaseBusinessRule[AdjustmentInput]):
    code = "BR-34"
    message = "% chiết khấu / phụ phí phải lớn hơn 0 và nhỏ hơn 100."
    field = "percent"

    def percent_ok(self, target: AdjustmentInput) -> bool:
        return Decimal(0) < target.percent < ONE

    def is_satisfied_by(self, target: AdjustmentInput) -> bool:
        return self.percent_ok(target) and bool(target.reason.strip()) and bool(target.order_ref.strip())

    def describe_violation(self, target: AdjustmentInput) -> str:
        return self.message if not self.percent_ok(target) else "Vui lòng nhập lý do và đơn hàng cụ thể."


class DeleteAdjustmentRule(BaseBusinessRule[PriceLine]):
    code = "BR-35"
    message = "Dòng đã có mã kế toán, không xoá được."

    def is_satisfied_by(self, target: PriceLine) -> bool:
        return target.line_type in ADJUSTMENT_TYPES and not target.has_accounting_code

    def describe_violation(self, target: PriceLine) -> str:
        if target.line_type not in ADJUSTMENT_TYPES:
            return f"Dòng {target.line_code} là dòng {target.line_type.value}, chỉ xoá được dòng Chiết khấu / Phụ phí."
        return f"Dòng {target.line_code} đã có mã kế toán, không xoá được."


class PriceLineBusiness(BaseBusiness[Yarn]):
    def trial_cost(self, regular: CostBreakdown, trial_factor: Decimal) -> CostBreakdown:
        """BR-30: mỗi khoản dòng Thí nghiệm = khoản của dòng Thường × hệ số thí nghiệm."""
        return stored_cost(regular.scaled(trial_factor))

    def adjustment_cost(self, regular: CostBreakdown, line_type: LineType, percent: Decimal) -> CostBreakdown:
        """BR-31: Chiết khấu = khoản dòng Thường × (1 − %); Phụ phí = × (1 + %)."""
        factor = ONE - percent if line_type == LineType.CHIET_KHAU else ONE + percent
        return stored_cost(regular.scaled(factor))

    def trial_code(self, yarn: Yarn) -> str:
        """BR-30: mã dòng thí nghiệm = mã dòng Thường + 'TN'."""
        return f"{yarn.yarn_code}{TRIAL_SUFFIX}"

    def status_for(self, yarn: Yarn) -> YarnStatus:
        """BR-32 / 4.12: bản có giá và có mã kế toán → 'Có mã kế toán', có giá chưa có mã → 'Đã tính giá'."""
        if yarn.status == YarnStatus.CHUA_TINH_DUOC or yarn.regular_line is None:
            return yarn.status
        return YarnStatus.CO_MA_KE_TOAN if yarn.is_locked else YarnStatus.DA_TINH_GIA

    def history(
        self, yarn: Yarn, line: PriceLine, event: PriceEvent, old: CostBreakdown | None, **context: object
    ) -> PriceHistory:
        return PriceHistory(
            factory_code=yarn.factory_code,
            yarn_code=yarn.yarn_code,
            line_code=line.line_code,
            line_type=line.line_type,
            event=event,
            old=old,
            new=line.cost,
            changed_by=str(context.get("changed_by", "")),
            batch_id=context.get("batch_id"),  # type: ignore[arg-type]
            effective_date=context.get("effective_date"),  # type: ignore[arg-type]
            reason=str(context.get("reason", "")),
        )

    def _set_line(
        self,
        lines: list[PriceLine],
        line: PriceLine,
        history: list[PriceHistory],
        yarn: Yarn,
        event: PriceEvent,
        **ctx: object,
    ) -> None:
        old = next((i for i, current in enumerate(lines) if current.line_code == line.line_code), None)
        if old is None:
            lines.append(line)
            # new line: "Tính lần đầu", except file import and UC-43 (BR-65) which keep their own event
            keep = (PriceEvent.NHAP_TU_FILE, PriceEvent.TINH_LAI_CHUA_TINH)
            first_event = event if event in keep else PriceEvent.TINH_LAN_DAU
            history.append(self.history(yarn, line, first_event, None, **ctx))
            return
        previous = lines[old]
        lines[old] = previous.model_copy(update={"cost": line.cost})
        if previous.total_vnd != line.total_vnd:
            history.append(self.history(yarn, lines[old], event, previous.cost, **ctx))

    def apply_result(
        self,
        yarn: Yarn,
        result: CostResult,
        trial_factor: Decimal,
        event: PriceEvent,
        now: datetime,
        effective_date: date,
        **ctx: object,
    ) -> tuple[Yarn, list[PriceHistory]]:
        """BR-14 / BR-16 / BR-30 / BR-31: cập nhật dòng Thường, TN, CK/PP theo kết quả tính (không đạt → giữ giá cũ)."""
        if not result.passed:
            update = {"status": YarnStatus.CHUA_TINH_DUOC, "status_reasons": result.reasons}
            return yarn.model_copy(update=update), []
        regular_cost = stored_cost(result.cost)
        lines = list(yarn.lines)
        history: list[PriceHistory] = []
        actor = str(ctx.get("changed_by", ""))
        ctx = {**ctx, "effective_date": effective_date}
        pending = yarn.pending_accounting_code
        regular = PriceLine(line_code=yarn.yarn_code, line_type=LineType.THUONG, cost=regular_cost, created_by=actor)
        if pending and yarn.regular_line is None:
            regular = regular.model_copy(
                update={"accounting_code": pending, "accounting_code_by": actor, "accounting_code_at": now}
            )
        self._set_line(lines, regular, history, yarn, event, **ctx)
        trial = PriceLine(
            line_code=self.trial_code(yarn),
            line_type=LineType.THI_NGHIEM,
            cost=self.trial_cost(regular_cost, trial_factor),
            created_by=actor,
        )
        self._set_line(lines, trial, history, yarn, event, **ctx)
        for line in [x for x in lines if x.line_type in ADJUSTMENT_TYPES]:
            updated = line.model_copy(
                update={
                    "cost": self.adjustment_cost(regular_cost, line.line_type, line.adjustment_percent or Decimal(0))
                }
            )
            self._set_line(lines, updated, history, yarn, event, **ctx)
        updated_yarn = yarn.model_copy(
            update={
                "lines": lines,
                "stage_details": [stored_detail(d) for d in result.details],
                "status_reasons": [],
                "pending_accounting_code": None if pending and yarn.regular_line is None else pending,
                # BR-65: a waiting yarn priced by UC-43 gets the chosen effective date as first priced date
                "first_priced_at": yarn.first_priced_at
                or (effective_date if event == PriceEvent.TINH_LAI_CHUA_TINH else now.date()),
                "effective_date": effective_date,
                "last_calculated_at": now,
                "status": YarnStatus.DA_TINH_GIA,
            }
        )
        return updated_yarn.model_copy(update={"status": self.status_for(updated_yarn)}), history

    def apply_trial_factor(self, yarn: Yarn, trial_factor: Decimal, **ctx: object) -> tuple[Yarn, list[PriceHistory]]:
        """BR-30: đổi hệ số thí nghiệm → cập nhật dòng Thí nghiệm của bản NSM."""
        regular = yarn.regular_line
        if regular is None:
            return yarn, []
        lines = list(yarn.lines)
        history: list[PriceHistory] = []
        trial = PriceLine(
            line_code=self.trial_code(yarn),
            line_type=LineType.THI_NGHIEM,
            cost=self.trial_cost(regular.cost, trial_factor),
        )
        self._set_line(lines, trial, history, yarn, PriceEvent.DOI_HE_SO_TN, **ctx)
        return yarn.model_copy(update={"lines": lines}), history

    def new_adjustment_line(
        self, yarn: Yarn, line_type: LineType, data: AdjustmentInput, actor: str
    ) -> tuple[Yarn, PriceLine]:
        """BR-31: mã = mã dòng Thường + ' (CKn)' / ' (PPn)', n = số lớn nhất đã dùng + 1 (không dùng lại)."""
        regular = yarn.regular_line
        assert regular is not None
        is_discount = line_type == LineType.CHIET_KHAU
        number = (yarn.max_ck_no if is_discount else yarn.max_pp_no) + 1
        line = PriceLine(
            line_code=f"{regular.line_code} ({'CK' if is_discount else 'PP'}{number})",
            line_type=line_type,
            adjustment_percent=data.percent,
            adjustment_reason=data.reason.strip(),
            order_ref=data.order_ref.strip(),
            cost=self.adjustment_cost(regular.cost, line_type, data.percent),
            created_by=actor,
        )
        counter = {"max_ck_no": number} if is_discount else {"max_pp_no": number}
        return yarn.model_copy(update={"lines": [*yarn.lines, line], **counter}), line

    def ensure_adjustment_valid(self, data: AdjustmentInput) -> None:
        """BR-34."""
        AdjustmentLineRule().check(data)

    def ensure_deletable(self, line: PriceLine) -> None:
        """BR-35."""
        DeleteAdjustmentRule().check(line)

    def sorted_lines(self, lines: Sequence[PriceLine]) -> list[PriceLine]:
        return sorted(lines, key=lambda line: (LINE_TYPE_ORDER[line.line_type], line.line_code))

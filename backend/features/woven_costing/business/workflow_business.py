"""BR-30..BR-38 statuses and versions, BR-40 OC, BR-41 costsheet number."""

import re
from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.numbers import round_half_up
from backend.features.woven_costing.constants import (
    COSTSHEET_PREFIX,
    COSTSHEET_SEQ_DIGITS,
    MIN_RETURN_REASON,
    OC_PATTERN,
)
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.costsheet import APPROVED_STATUSES, OPEN_STATUSES, Costsheet
from backend.features.woven_costing.models.dyeing_job import DyeingJob
from backend.features.woven_costing.models.enums import CostsheetStatus

S = CostsheetStatus
# BR-30 allowed transitions
TRANSITIONS = {
    S.NHAP: (S.CHO_DUYET, S.HUY),
    S.CHO_DUYET: (S.DA_DUYET, S.TRA_LAI, S.HUY),
    S.TRA_LAI: (S.NHAP, S.CHO_DUYET, S.HUY),
    S.DA_DUYET: (S.DA_CHOT_DON, S.HUY, S.DA_THAY_THE),
    S.DA_CHOT_DON: (S.DA_THAY_THE,),
    S.HUY: (),
    S.DA_THAY_THE: (),
}
_SPACES = re.compile(r"\s+")
_BRACKETS = re.compile(r"\([^)]*\)")


class TransitionRule(BaseBusinessRule[Check]):
    """Target text = current status, other = wanted status."""

    code = "BR-30"
    message = "Không thể chuyển trạng thái costsheet."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f'Không thể chuyển costsheet từ "{target.text}" sang "{target.other}".'


class EditableRule(BaseBusinessRule[Check]):
    code = "BR-31"
    message = "Costsheet không sửa được."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Costsheet đang ở trạng thái {target.text}, không sửa được."


class PendingRule(BaseBusinessRule[Check]):
    code = "BR-32"
    message = "Costsheet không ở trạng thái Chờ duyệt."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class ReturnReasonRule(BaseBusinessRule[str]):
    code = "BR-33"
    message = "Vui lòng nhập lý do trả lại."
    field = "reason"

    def is_satisfied_by(self, target: str) -> bool:
        return len(target.strip()) >= MIN_RETURN_REASON


class CancelReasonRule(BaseBusinessRule[str]):
    code = "BR-36"
    message = "Vui lòng nhập lý do hủy."
    field = "reason"

    def is_satisfied_by(self, target: str) -> bool:
        return bool(target.strip())


class CancelStatusRule(BaseBusinessRule[Check]):
    code = "BR-36"
    message = "Costsheet đã chốt đơn không hủy được."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class CloseOrderRule(BaseBusinessRule[Check]):
    code = "BR-36"
    message = "Cần nhập OC trước khi chốt đơn."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok


class OneOpenVersionRule(BaseBusinessRule[Check]):
    """Target text = costsheet no, other = open version."""

    code = "BR-37"
    message = "Costsheet đang có phiên bản chưa duyệt. Hãy hoàn tất phiên bản đó trước."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Costsheet {target.text} đang có phiên bản {target.other} chưa duyệt. Hãy hoàn tất phiên bản đó trước."


class OcFormatRule(BaseBusinessRule[str]):
    """Target = OC after cleaning."""

    code = "BR-40"
    message = "OC sai định dạng. Ví dụ đúng: KDV10-SX-LO-0726-6564.1"
    field = "oc_no"

    def is_satisfied_by(self, target: str) -> bool:
        return bool(re.match(OC_PATTERN, target))

    def describe_violation(self, target: str) -> str:
        return f'OC "{target}" sai định dạng. Ví dụ đúng: KDV10-SX-LO-0726-6564.1'


class OcUniqueRule(BaseBusinessRule[Check]):
    """Target text = OC, other = costsheet number where it is already closed."""

    code = "BR-40"
    message = "OC đã được chốt ở costsheet khác."
    field = "oc_no"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"OC {target.text} đã được chốt ở costsheet {target.other}."


class WorkflowBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (TransitionRule(),)

    def ensure_transition(self, sheet: Costsheet | DyeingJob, to: CostsheetStatus) -> None:
        """BR-30: only the transitions of the status diagram."""
        ok = to in TRANSITIONS.get(sheet.status, ())
        TransitionRule().check(Check(ok=ok, text=sheet.status.value, other=to.value))

    def ensure_editable(self, sheet: Costsheet | DyeingJob) -> None:
        """BR-31 / BR-38 / BR-39: only Nháp / Trả lại are changed (and recalculated)."""
        EditableRule().check(Check(ok=sheet.is_editable_status, text=sheet.status.value))

    def ensure_pending(self, sheet: Costsheet | DyeingJob) -> None:
        """BR-32."""
        PendingRule().check(Check(ok=sheet.status == CostsheetStatus.CHO_DUYET))

    def ensure_return_reason(self, reason: str) -> None:
        """BR-33: at least 5 characters."""
        ReturnReasonRule().check(reason)

    def ensure_cancel(self, sheet: Costsheet | DyeingJob, reason: str) -> None:
        """BR-36: reason required; Đã chốt đơn / Hủy / Đã thay thế cannot be cancelled."""
        CancelStatusRule().check(Check(ok=sheet.status not in (S.DA_CHOT_DON, S.HUY, S.DA_THAY_THE)))
        CancelReasonRule().check(reason)

    def ensure_can_close(self, sheet: Costsheet, oc_no: str) -> None:
        """BR-36: close the order only when Đã duyệt and with a valid OC."""
        self.ensure_transition(sheet, S.DA_CHOT_DON)
        CloseOrderRule().check(Check(ok=bool(oc_no)))

    def open_version(self, versions: list[Costsheet], excluding_id: str = "") -> Costsheet | None:
        """BR-37: the version in Nháp / Chờ duyệt / Trả lại, if any."""
        return next((v for v in versions if v.status in OPEN_STATUSES and v.id != excluding_id), None)

    def ensure_no_open_version(self, versions: list[Costsheet]) -> None:
        """BR-37: one open version at a time; a new version only from the latest approved / closed one."""
        current = self.open_version(versions)
        no = versions[0].costsheet_no if versions else ""
        OneOpenVersionRule().check(Check(ok=current is None, text=no, other=str(current.version) if current else ""))
        latest = max(versions, key=lambda v: v.version) if versions else None
        if latest is not None and latest.status not in APPROVED_STATUSES:
            TransitionRule().check(Check(ok=False, text=latest.status.value, other=S.NHAP.value))

    def clean_oc(self, raw: str) -> str:
        """BR-40: remove spaces, text in brackets and trailing commas."""
        text = _SPACES.sub("", _BRACKETS.sub("", raw or ""))
        return text.rstrip(",;").upper()

    def ensure_oc(self, oc_no: str) -> None:
        OcFormatRule().check(oc_no)

    def ensure_oc_free(self, oc_no: str, sheet: Costsheet, others: list[Costsheet]) -> None:
        """BR-40: one OC is closed on one costsheet only (latest version, Đã chốt đơn)."""
        taken = next(
            (
                o
                for o in others
                if o.oc_no == oc_no and o.status == S.DA_CHOT_DON and o.costsheet_no != sheet.costsheet_no
            ),
            None,
        )
        OcUniqueRule().check(Check(ok=taken is None, text=oc_no, other=taken.costsheet_no if taken else ""))

    def main_oc(self, oc_no: str) -> str:
        """BR-40: Main OC = part before the dot."""
        return oc_no.split(".")[0]

    def costsheet_number(self, customer_code: str, year: int, existing: list[str]) -> str:
        """BR-41: CS-<customer code>-YYYY-NNNNN, NNNNN increasing in the year for every customer."""
        sequences = []
        for number in existing:
            parts = number.split("-")
            if len(parts) >= 4 and parts[-2] == str(year) and parts[-1].isdigit():
                sequences.append(int(parts[-1]))
        next_seq = max(sequences, default=0) + 1
        return f"{COSTSHEET_PREFIX}-{customer_code}-{year}-{next_seq:0{COSTSHEET_SEQ_DIGITS}d}"

    def price_signature(self, sheet: Costsheet) -> tuple[Decimal, Decimal, Decimal]:
        """BR-35: sell price and COGS rounded to the dong, GP% rounded to 0.01%."""
        result = sheet.result
        return (
            round_half_up(result.sell_price_vnd),
            round_half_up(result.cogs_vnd),
            round_half_up(result.gp_pct * 100, 2),
        )

    def auto_approves(self, sheet: Costsheet, versions: list[Costsheet]) -> bool:
        """BR-35: version >= 2 is approved automatically when sell price, COGS and GP% equal the last approved one."""
        if sheet.version < 2:
            return False
        approved = [v for v in versions if v.status in APPROVED_STATUSES and v.version < sheet.version]
        if not approved:
            return False
        last = max(approved, key=lambda v: v.version)
        return self.price_signature(sheet) == self.price_signature(last)

"""2026-11-27 approving from "Việc chờ tôi": BR-101 Cần chú ý, BR-102 approving many, BR-103 previous approved version.
The approval of ONE costsheet / job order (UC-21 / UC-43) is also built here so that both ways stay the same."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, utc_now
from backend.features.woven_costing.models.costsheet import Costsheet, CostsheetHistory
from backend.features.woven_costing.models.dyeing_job import DyeingJob
from backend.features.woven_costing.models.enums import CostsheetStatus, DyePlant, HistoryAction, ShrinkageException

S = CostsheetStatus
SEP = " · "
PREVIOUS_STATUSES = (S.DA_DUYET, S.DA_CHOT_DON, S.DA_THAY_THE)  # BR-103


def pct_text(rate: Decimal) -> str:
    """0.125 -> "12,5%" (Vietnamese decimal comma, no useless zeros)."""
    text = f"{rate * 100:.2f}".rstrip("0").rstrip(".")
    return f"{text.replace('.', ',')}%"


def failed_text(label: str, reason: str) -> str:
    """BR-102 message of one costsheet / job order that could not be approved."""
    return f"Không duyệt được {label}: {reason}"


class ApprovalBusiness(BaseBusiness[Costsheet]):
    # ---- BR-101 --------------------------------------------------------------------------------------------------
    def attention(self, sheet: Costsheet) -> str:
        """BR-101 costsheet: the short "Cần chú ý" text (empty when nothing needs a look)."""
        r = sheet.result
        items: list[str] = []
        if r.gp_below:
            items.append(f"GP dưới ngưỡng {pct_text(r.gp_threshold)}")
        if r.op_below:
            items.append(f"OP dưới ngưỡng {pct_text(r.op_threshold)}")
        if r.low_shrinkage or sheet.shrinkage_exception != ShrinkageException.NONE:
            items.append(f"Độ co {pct_text(r.shrinkage)}")
        if sheet.parameter_overrides:
            items.append(f"Sửa {len(sheet.parameter_overrides)} tham số")
        if sheet.fabric_overridden:
            items.append("Sửa thông số vải")
        dyeing = sheet.tcdn_dyeing if sheet.dye_plant == DyePlant.TCDN else sheet.hcm_dyeing
        if dyeing.extra_cost is not None:
            items.append("Sửa chi phí phát sinh")
        return SEP.join(items)

    def job_attention(self, job: DyeingJob) -> str:
        """BR-101 dyeing job order: %GP of the order, lines under the threshold, lines with their own quote."""
        r = job.result
        items: list[str] = []
        if r.calculated and r.gp_below:
            items.append(f"%GP phiếu dưới ngưỡng {pct_text(r.gp_threshold)}")
        low = sum(1 for line in r.lines if line.gp_below)
        if low:
            items.append(f"{low} dòng %GP dưới ngưỡng")
        quoted = sum(1 for line in r.lines if line.quoted)
        if quoted:
            items.append(f"{quoted} dòng báo giá riêng")
        return SEP.join(items)

    # ---- BR-103 --------------------------------------------------------------------------------------------------
    def previous_approved(self, sheet: Costsheet, versions: Sequence[Costsheet]) -> Costsheet | None:
        """BR-103: the latest earlier version that was approved (Đã duyệt, Đã chốt đơn, Đã thay thế); None for v1."""
        earlier = [v for v in versions if v.version < sheet.version and v.status in PREVIOUS_STATUSES]
        return max(earlier, key=lambda v: v.version) if earlier else None

    # ---- UC-21 / UC-43 (one) and BR-102 (many) -------------------------------------------------------------------
    def approved_sheet(self, sheet: Costsheet, who: str, name: str) -> Costsheet:
        return sheet.model_copy(
            update={"status": S.DA_DUYET, "approved_by": who, "approved_by_name": name, "approved_at": utc_now()}
        )

    def approved_job(self, job: DyeingJob, who: str, name: str) -> DyeingJob:
        return job.model_copy(
            update={"status": S.DA_DUYET, "approved_by": who, "approved_by_name": name, "approved_at": utc_now()}
        )

    def approve_history(self, sheet: Costsheet, who: str, name: str, comment: str = "") -> CostsheetHistory:
        return CostsheetHistory(
            costsheet_no=sheet.costsheet_no, version=sheet.version, action=HistoryAction.APPROVE, by=who, by_name=name,
            comment=comment,
        )  # fmt: skip

    def summary(self, approved: int, failed: int, what: str) -> str:
        """BR-102 message: "Đã duyệt N <what>." (+ how many could not be approved)."""
        text = f"Đã duyệt {approved} {what}."
        return f"{text} {failed} phiếu không duyệt được." if failed else text

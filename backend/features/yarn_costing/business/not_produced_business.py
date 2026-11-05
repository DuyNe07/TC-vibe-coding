"""BR-72..BR-75 Trạng thái "Không sản xuất" (bổ sung 2026-11-05): đánh dấu, chặn thao tác, bỏ đánh dấu, đọc file."""

from collections.abc import Sequence
from datetime import datetime

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import FactoryCode, PriceEvent, YarnStatus
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.yarn import CostBreakdown, Yarn
from backend.shared.utils.text import normalize_key

MARKABLE = (YarnStatus.DA_TINH_GIA, YarnStatus.CHUA_TINH_DUOC)
MAX_REASON = 500
MSG_REASON = "Vui lòng nhập lý do."
MSG_REASON_LONG = "Lý do tối đa 500 ký tự."
MSG_WAITING = "Mã {code} đang 'Chờ xưởng xem'. Hãy dùng Từ chối."
MSG_ACCOUNTING = (
    "Mã {code} có mã kế toán ({accounting}) nên không đánh dấu Không sản xuất được. Vui lòng xoá mã kế toán trước."
)
MSG_STATUS = "Mã {code} đang ở trạng thái '{status}' nên không đánh dấu Không sản xuất được."
MSG_ALREADY = "Mã {code} đã là 'Không sản xuất'."
MSG_BLOCKED = "Mã {code} đang 'Không sản xuất'. Vui lòng bỏ đánh dấu trước khi thao tác."
MSG_NOT_MARKED = "Mã {code} không ở trạng thái 'Không sản xuất'."
MSG_DUPLICATE = "Mã '{code}' bị trùng trong file."
MSG_UNKNOWN = "Không có mã '{code}' ở xưởng {factory}."
NOTE_ALREADY = "đã là Không sản xuất"


class NotProducedBusiness(BaseBusiness[Yarn]):
    # ---- BR-72 / BR-74: a base code and all its NSM revisions move together ----
    def family(self, yarns: Sequence[Yarn], yarn: Yarn) -> list[Yarn]:
        members = [y for y in yarns if y.factory_code == yarn.factory_code and y.base_code == yarn.base_code]
        return sorted(members, key=lambda y: y.revision_no)

    def clean_reason(self, reason: str) -> str:
        text = (reason or "").strip()
        if not text:
            raise YarnValidationError(MSG_REASON)
        if len(text) > MAX_REASON:
            raise YarnValidationError(MSG_REASON_LONG)
        return text

    def mark_problem(self, family: Sequence[Yarn]) -> str | None:
        """BR-72: why the family cannot be marked, or None. Already marked → MSG_ALREADY."""
        base = family[0]
        if all(y.status == YarnStatus.KHONG_SAN_XUAT for y in family):
            return MSG_ALREADY.format(code=base.yarn_code)
        for y in family:
            if y.status == YarnStatus.CHO_XUONG_XEM:
                return MSG_WAITING.format(code=y.yarn_code)
            coded = next((line.accounting_code for line in y.lines if line.accounting_code), None)
            if coded:
                return MSG_ACCOUNTING.format(code=y.yarn_code, accounting=coded)
            if y.status not in MARKABLE and y.status != YarnStatus.KHONG_SAN_XUAT:
                return MSG_STATUS.format(code=y.yarn_code, status=y.status.value)
        return None

    def mark(
        self, family: Sequence[Yarn], reason: str, user_label: str, now: datetime
    ) -> tuple[list[Yarn], list[PriceHistory], int]:
        """BR-72: every price line with a total > 0 → one history row (old price → 0); lines and stage details are
        removed; status 'Không sản xuất'. Name, NSM, components, packaging, first priced date and the waiting
        accounting code (BR-70) are kept."""
        updated, history = [], []
        removed = 0
        for y in family:
            if y.status == YarnStatus.KHONG_SAN_XUAT:
                continue
            for line in y.lines:
                removed += 1
                if line.total_vnd > 0:
                    history.append(
                        PriceHistory(
                            factory_code=y.factory_code,
                            yarn_code=y.yarn_code,
                            line_code=line.line_code,
                            line_type=line.line_type,
                            changed_at=now,
                            changed_by=user_label,
                            event=PriceEvent.KHONG_SAN_XUAT,
                            effective_date=now.date(),
                            old=line.cost,
                            new=CostBreakdown(),
                            reason=reason,
                        )
                    )
            updated.append(
                y.model_copy(
                    update={
                        "status": YarnStatus.KHONG_SAN_XUAT,
                        "status_reasons": [],
                        "lines": [],
                        "stage_details": [],
                        "not_produced_reason": reason,
                        "not_produced_by": user_label,
                        "not_produced_at": now,
                    }
                )
            )
        return updated, history, removed

    def ensure_active(self, yarn: Yarn) -> None:
        """BR-73: every action on a 'Không sản xuất' yarn is refused (only unmarking is allowed)."""
        if yarn.status == YarnStatus.KHONG_SAN_XUAT:
            raise YarnValidationError(MSG_BLOCKED.format(code=yarn.yarn_code))

    def to_recalculate(self, family: Sequence[Yarn]) -> list[Yarn]:
        """BR-74: marked members back to 'Chưa tính được' with the marking cleared, ready to be recalculated."""
        marked = [y for y in family if y.status == YarnStatus.KHONG_SAN_XUAT]
        if not marked:
            raise YarnValidationError(MSG_NOT_MARKED.format(code=family[0].yarn_code))
        return [
            y.model_copy(
                update={
                    "status": YarnStatus.CHUA_TINH_DUOC,
                    "not_produced_reason": "",
                    "not_produced_by": "",
                    "not_produced_at": None,
                }
            )
            for y in marked
        ]

    # ---- BR-75: file rows ----
    def plan_file(
        self, rows: Sequence[tuple[int, str, str]], factory: FactoryCode, yarns: Sequence[Yarn], normalize
    ) -> tuple[list[tuple[int, list[Yarn], str]], list[tuple[int, str, str]], list[tuple[int, str, str]]]:
        """rows = (excel_row, raw code, reason). Returns (valid: row, family, reason), rejected and skipped
        (row, code, reason)."""
        by_code = {normalize_key(y.yarn_code): y for y in yarns if y.factory_code == factory}
        parsed = []
        for excel_row, raw, reason in rows:
            code = normalize(raw) if raw else ""
            if not code:
                continue
            yarn = by_code.get(normalize_key(code))
            parsed.append((excel_row, code, (reason or "").strip(), yarn))
        bases: dict[str, int] = {}
        for _, _, _, yarn in parsed:
            if yarn is not None:
                bases[yarn.base_code] = bases.get(yarn.base_code, 0) + 1
        counts: dict[str, int] = {}
        for _, code, _, _ in parsed:
            counts[normalize_key(code)] = counts.get(normalize_key(code), 0) + 1
        valid, rejected, skipped = [], [], []
        for excel_row, code, reason, yarn in parsed:
            shown = yarn.yarn_code if yarn else code
            if counts[normalize_key(code)] > 1 or (yarn is not None and bases[yarn.base_code] > 1):
                rejected.append((excel_row, shown, MSG_DUPLICATE.format(code=shown)))
                continue
            if yarn is None:
                rejected.append((excel_row, code, MSG_UNKNOWN.format(code=code, factory=factory.value)))
                continue
            if not reason:
                rejected.append((excel_row, shown, MSG_REASON))
                continue
            if len(reason) > MAX_REASON:
                rejected.append((excel_row, shown, MSG_REASON_LONG))
                continue
            family = self.family(yarns, yarn)
            problem = self.mark_problem(family)
            if problem == MSG_ALREADY.format(code=family[0].yarn_code):
                skipped.append((excel_row, shown, NOTE_ALREADY))
            elif problem:
                rejected.append((excel_row, shown, problem))
            else:
                valid.append((excel_row, family, reason))
        return valid, rejected, skipped

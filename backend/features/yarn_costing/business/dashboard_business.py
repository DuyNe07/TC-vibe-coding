"""BR-53: chỉ số dashboard (sợi báo giá, có đơn hàng, yêu cầu mới, khả năng đáp ứng, đang chờ, lần tính lại)."""

from collections import Counter
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.models.analysis import DashboardStats, WeeklyStat
from backend.features.yarn_costing.models.enums import LineType, YarnOrigin, YarnStatus
from backend.features.yarn_costing.models.price_history import PriceHistory
from backend.features.yarn_costing.models.recalc_batch import RecalcBatch
from backend.features.yarn_costing.models.yarn import Yarn

HANDLED_STATUSES = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN, YarnStatus.CHUA_TINH_DUOC)
HUNDRED = Decimal(100)


def local_date(moment: datetime) -> date:
    return moment.astimezone().date()


class DashboardBusiness(BaseBusiness[Yarn]):
    def ratio(self, part: int, whole: int) -> Decimal | None:
        return Decimal(part) / Decimal(whole) * HUNDRED if whole else None

    def fulfilment(self, requests: Sequence[Yarn]) -> Decimal | None:
        """BR-53 (4): đã lưu NSM ÷ (đã lưu NSM + bị từ chối) × 100% (không có yêu cầu đã xử lý → '-')."""
        handled = sum(1 for y in requests if y.status in HANDLED_STATUSES)
        rejected = sum(1 for y in requests if y.status == YarnStatus.TU_CHOI)
        return self.ratio(handled, handled + rejected)

    def weekly(self, requests: Sequence[Yarn], date_from: date, date_to: date) -> list[WeeklyStat]:
        """BR-53: số yêu cầu mới và khả năng đáp ứng theo tuần (tuần bắt đầu thứ Hai)."""
        weeks: list[WeeklyStat] = []
        start = date_from - timedelta(days=date_from.weekday())
        while start <= date_to:
            end = start + timedelta(days=6)
            members = [y for y in requests if start <= local_date(y.requested_at) <= end]
            weeks.append(
                WeeklyStat(week_start=start, new_requests=len(members), fulfilment_ratio=self.fulfilment(members))
            )
            start = end + timedelta(days=1)
        return weeks

    def last_batch(self, batches: Sequence[RecalcBatch], date_from: date, date_to: date) -> RecalcBatch | None:
        """BR-53 (6): lần tính lại gần nhất trong khoảng ngày."""
        in_range = [b for b in batches if date_from <= local_date(b.run_at) <= date_to]
        return max(in_range, key=lambda b: b.run_at, default=None)

    def batch_changes(self, batch: RecalcBatch, history: Sequence[PriceHistory]) -> tuple[int, int, Decimal | None]:
        """BR-53 (6): số dòng tăng / giảm, chênh lệch % trung bình của các dòng Thường thay đổi."""
        entries = [h for h in history if h.batch_id == batch.batch_code and h.old is not None]
        up = sum(1 for h in entries if h.new.total > h.old.total)  # type: ignore[union-attr]
        down = sum(1 for h in entries if h.new.total < h.old.total)  # type: ignore[union-attr]
        percents = [
            (h.new.total - h.old.total) / h.old.total * HUNDRED  # type: ignore[union-attr]
            for h in entries
            if h.line_type == LineType.THUONG and h.old is not None and h.old.total != 0
        ]
        average = sum(percents, Decimal(0)) / len(percents) if percents else None
        return up, down, average

    def stats(
        self,
        yarns: Sequence[Yarn],
        batches: Sequence[RecalcBatch],
        history: Sequence[PriceHistory],
        date_from: date,
        date_to: date,
    ) -> DashboardStats:
        """BR-53 (1)-(6) cho khoảng ngày [từ, đến] (danh sách đã lọc theo xưởng)."""
        quoted = [y for y in yarns if y.is_base and y.first_priced_at and date_from <= y.first_priced_at <= date_to]
        ordered = [y for y in quoted if y.is_locked]
        requests = [
            y
            for y in yarns
            if y.origin == YarnOrigin.YEU_CAU_SALES and date_from <= local_date(y.requested_at) <= date_to
        ]
        last = self.last_batch(batches, date_from, date_to)
        up, down, average = self.batch_changes(last, history) if last else (0, 0, None)
        status_counts = Counter(y.status.value for y in yarns for _ in y.lines)
        return DashboardStats(
            quoted_count=len(quoted),
            ordered_count=len(ordered),
            ordered_ratio=self.ratio(len(ordered), len(quoted)),
            new_request_count=len(requests),
            fulfilment_ratio=self.fulfilment(requests),
            waiting_count=sum(1 for y in yarns if y.status == YarnStatus.CHO_XUONG_XEM),
            weekly=self.weekly(requests, date_from, date_to),
            status_counts=dict(status_counts),
            last_batch_code=last.batch_code if last else None,
            last_batch_up=up,
            last_batch_down=down,
            last_batch_avg_percent=average,
        )

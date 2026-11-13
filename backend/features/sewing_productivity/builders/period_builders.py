"""UC-29: the periods of Screen 4 -> one table per figure (BR-69) with its cards (BR-70, BR-71). The figures are
declared once, here."""

from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.builders.display import KIND_DECIMALS, as_float, is_below, suffix_of
from backend.features.sewing_productivity.dto.monthly_dto import (
    CHANGEOVER_PER_LINE_DAY,
    MonthlyReportResponse,
    PeriodCardDTO,
    PeriodMetricDTO,
    PeriodValueRowDTO,
)
from backend.features.sewing_productivity.models.enums import NumberKind
from backend.features.sewing_productivity.models.report_values import PeriodSummaries

# label, attribute of FactorySummary, format, attribute of the BR-28 result; in the order of the screen (BR-69)
PERIOD_ROWS = (
    ("MO 8h", "mo8h", NumberKind.MONEY, "mo8h_assessment"),
    ("Hiệu suất B", "efficiency_b", NumberKind.PERCENT, "efficiency_b_assessment"),
    ("Direct worker", "direct_workers", NumberKind.PEOPLE, None),
    ("%Direct labor", "direct_labor", NumberKind.PERCENT, None),  # BR-77: cards in the Direct worker tab only
    ("Sản lượng", "output", NumberKind.INTEGER, None),
    ("Tiền CM", "cm_earning", NumberKind.MONEY, None),
    ("Giá CM trung bình", "average_cm_price", NumberKind.MONEY, None),
    ("SMV bình quân", "average_smv", NumberKind.MONEY, None),
    ("Giờ làm trung bình", "average_hours", NumberKind.MONEY, None),
    # BR-89 (thêm 2026-11-13): the same match as the Screen 1 row (BR-86), shown as "Matching strength"
    ("Tỷ lệ đúng sở trường", "strength_match", NumberKind.PERCENT, None),
    (CHANGEOVER_PER_LINE_DAY, "changeover_per_line_day", NumberKind.KPI, None),  # BR-89 (thêm 2026-11-13)
)
PERIOD_FIELDS = tuple(field for _label, field, _kind, _assessment in PERIOD_ROWS)


class PeriodReportResponseBuilder(BaseBuilder[MonthlyReportResponse]):
    def __init__(
        self,
        periods: list[PeriodSummaries],
        compare_label: str = "",
        changes: dict[tuple[str, str], Decimal | None] | None = None,
        rising_is_good: dict[str, bool | None] | None = None,
    ) -> None:
        self.periods = periods
        self.compare_label = compare_label
        self.changes = changes or {}
        self.rising_is_good = rising_is_good or {}

    def build(self) -> MonthlyReportResponse:
        columns = [summary.column for summary in self.periods[0].summaries] if self.periods else []
        metrics = []
        for label, field, kind, assessment in PERIOD_ROWS:
            rows = [self._row(item, field, assessment) for item in self.periods]
            metrics.append(
                PeriodMetricDTO(
                    metric=label,
                    decimals=KIND_DECIMALS[kind],
                    suffix=suffix_of(kind),
                    rows=rows,
                    cards=self._cards(rows[-1], field) if rows else [],
                    compare_label=self.compare_label,
                    rising_is_good=self.rising_is_good.get(field),
                )
            )
        return MonthlyReportResponse(factories=[], has_data=bool(self.periods), columns=columns, period_metrics=metrics)

    @staticmethod
    def _row(item: PeriodSummaries, field: str, assessment: str | None) -> PeriodValueRowDTO:
        return PeriodValueRowDTO(
            period=item.period.label,
            start=item.period.from_date,
            values={summary.column: as_float(getattr(summary, field)) for summary in item.summaries},
            below={
                summary.column: is_below(getattr(summary, assessment)) if assessment else False
                for summary in item.summaries
            },
        )

    def _cards(self, last: PeriodValueRowDTO, field: str) -> list[PeriodCardDTO]:
        """BR-70, BR-71 the last period of each column (same number and 🔴 as its table row) with its change."""
        return [
            PeriodCardDTO(
                column=column,
                value=value,
                change=as_float(self.changes.get((field, column))),
                below=last.below.get(column, False),
            )
            for column, value in last.values.items()
        ]

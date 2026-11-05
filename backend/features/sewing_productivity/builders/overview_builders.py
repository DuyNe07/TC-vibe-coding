"""Overview table, daily factory table and charts -> response DTOs. The table rows are declared once, here."""

from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.builders.display import KIND_DECIMALS, as_float, is_below, suffix_of
from backend.features.sewing_productivity.dto.overview_dto import (
    ChartPointDTO,
    ChartsResponse,
    FactoryOutputDTO,
    OverviewMetricDTO,
    OverviewResponse,
    RankedLineDTO,
)
from backend.features.sewing_productivity.models.enums import NumberKind
from backend.features.sewing_productivity.models.report_values import (
    DailyFactorySummary,
    FactoryDayStat,
    FactorySummary,
    RankedLine,
)

# label, attribute, format, attribute of the BR-28 result
OVERVIEW_ROWS = (
    ("Mục tiêu A", "target_a", NumberKind.INTEGER, None),
    ("Sản lượng", "output", NumberKind.INTEGER, None),
    ("Mục tiêu hiệu suất", "efficiency_target", NumberKind.PERCENT, None),
    ("Hiệu suất A", "efficiency_a", NumberKind.PERCENT, "efficiency_a_assessment"),
    ("% so với mục tiêu của hiệu suất A", "efficiency_a_vs_target", NumberKind.PERCENT, None),
    ("Mục tiêu B", "target_b", NumberKind.INTEGER, None),
    ("Hiệu suất B", "efficiency_b", NumberKind.PERCENT, "efficiency_b_assessment"),
    ("% so với mục tiêu của hiệu suất B", "efficiency_b_vs_target", NumberKind.PERCENT, None),
    ("Tiền CM", "cm_earning", NumberKind.MONEY, None),
    ("Mục tiêu MO 8h", "mo8h_target", NumberKind.MONEY, None),
    ("MO 8h", "mo8h", NumberKind.MONEY, "mo8h_assessment"),
    ("% so với mục tiêu của MO 8h", "mo8h_vs_target", NumberKind.PERCENT, None),
    ("Giá CM trung bình", "average_cm_price", NumberKind.MONEY, None),
    ("Giờ làm trung bình", "average_hours", NumberKind.MONEY, None),
    ("Tỷ lệ đúng sở trường", "strength_match", NumberKind.PERCENT, None),
    ("Đổi mã hàng tuần", "weekly_changeover", NumberKind.INTEGER, None),
    ("Đổi mã hàng tuần trên chuyền", "weekly_changeover_per_line", NumberKind.MONEY, None),
)
DAILY_ROWS = (
    ("MO", "mo", NumberKind.MONEY, None),
    ("Giờ làm", "hours", NumberKind.MONEY, None),
    ("Target MO 8h", "target_mo8h", NumberKind.MONEY, None),
    ("MO 8h", "mo8h", NumberKind.MONEY, "mo8h_assessment"),
    ("% so với Target MO 8h", "mo8h_vs_target", NumberKind.PERCENT, None),
    ("Mục tiêu sản lượng", "target_output", NumberKind.INTEGER, None),
    ("Sản lượng", "output", NumberKind.INTEGER, None),
    ("Hiệu suất A", "efficiency_a", NumberKind.PERCENT, "efficiency_a_assessment"),
    ("Hiệu suất B", "efficiency_b", NumberKind.PERCENT, "efficiency_b_assessment"),
    ("Tỷ lệ đúng sở trường", "strength_match", NumberKind.PERCENT, None),
    ("Số thợ", "workers", NumberKind.PEOPLE, None),
)
# label, attribute of the BR-28 result: the extra rows of the Excel files (section 5.2)
ASSESSMENT_ROWS = (
    ("Đánh giá hiệu suất A", "efficiency_a_assessment"),
    ("Đánh giá hiệu suất B", "efficiency_b_assessment"),
    ("Đánh giá MO 8h", "mo8h_assessment"),
)


def metric_rows(
    spec: tuple[tuple[str, str, NumberKind, str | None], ...], summaries: list[FactorySummary | DailyFactorySummary]
) -> list[OverviewMetricDTO]:
    """One DTO per row of the table, one value and one flag per factory."""
    return [
        OverviewMetricDTO(
            metric=label,
            decimals=KIND_DECIMALS[kind],
            suffix=suffix_of(kind),
            values={summary.factory.value: as_float(getattr(summary, field)) for summary in summaries},
            below={
                summary.factory.value: is_below(getattr(summary, assessment)) if assessment else False
                for summary in summaries
            },
        )
        for label, field, kind, assessment in spec
    ]


class OverviewResponseBuilder(BaseBuilder[OverviewResponse]):
    def __init__(self, summaries: list[FactorySummary], note: str, has_data: bool) -> None:
        self.summaries = summaries
        self.note = note
        self.has_data = has_data

    def build(self) -> OverviewResponse:
        return OverviewResponse(
            metrics=metric_rows(OVERVIEW_ROWS, self.summaries), note=self.note, has_data=self.has_data
        )


class ChartsResponseBuilder(BaseBuilder[ChartsResponse]):
    def __init__(
        self,
        days: list[FactoryDayStat],
        summaries: list[FactorySummary],
        top_lines: list[RankedLine],
        bottom_lines: list[RankedLine],
        not_applicable_message: str,
        has_data: bool,
    ) -> None:
        self.days = days
        self.summaries = summaries
        self.top_lines = top_lines
        self.bottom_lines = bottom_lines
        self.not_applicable_message = not_applicable_message
        self.has_data = has_data

    def build(self) -> ChartsResponse:
        return ChartsResponse(
            efficiency_a=self._series("efficiency_a"),
            efficiency_b=self._series("efficiency_b"),
            mo8h=self._series("mo8h"),
            output_vs_target=[] if self.not_applicable_message else self._outputs(),
            top_lines=self._ranked(self.top_lines),
            bottom_lines=self._ranked(self.bottom_lines),
            not_applicable_message=self.not_applicable_message,
            has_data=self.has_data,
        )

    def _series(self, field: str) -> list[ChartPointDTO]:
        return [
            ChartPointDTO(day=stat.day, factory=stat.factory.value, value=float(getattr(stat, field)))
            for stat in self.days
            if getattr(stat, field) is not None
        ]

    def _outputs(self) -> list[FactoryOutputDTO]:
        return [
            FactoryOutputDTO(
                factory=summary.factory.value,
                output=float(summary.output or Decimal(0)),
                target_a=as_float(summary.target_a),
            )
            for summary in self.summaries
            if summary.output is not None or summary.target_a is not None
        ]

    @staticmethod
    def _ranked(lines: list[RankedLine]) -> list[RankedLineDTO]:
        return [RankedLineDTO(factory=item.factory.value, line=item.line, value=float(item.value)) for item in lines]

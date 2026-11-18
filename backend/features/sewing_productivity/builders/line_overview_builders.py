"""BR-83, BR-84, section 4.11: Line Detail rows, line orders and line strengths -> DTOs (sửa 2026-11-12)."""

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.builders.display import as_float, is_below
from backend.features.sewing_productivity.dto.line_detail_dto import (
    LineDetailResponse,
    LineOrderDTO,
    LineOverviewDTO,
    LineStrengthDTO,
    LineTrendPointDTO,
)
from backend.features.sewing_productivity.models.clean_values import line_sort_key
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.report_values import LineOrder, LineOverview, LineTrendPoint
from backend.features.sewing_productivity.models.source_records import LineStrength


def overview_dtos(rows: list[LineOverview]) -> list[LineOverviewDTO]:
    return [
        LineOverviewDTO(
            line=row.line,
            is_total=row.is_total,
            output=as_float(row.output),
            efficiency=as_float(row.efficiency),
            mo8h=as_float(row.mo8h),
            hours=as_float(row.hours),
            matching_ratio=as_float(row.matching_ratio),
            changeover=row.changeover,
            efficiency_below=is_below(row.efficiency_assessment),
            mo8h_below=is_below(row.mo8h_assessment),
        )
        for row in rows
    ]


def order_dtos(orders: list[LineOrder]) -> list[LineOrderDTO]:
    return [
        LineOrderDTO(
            line=order.line,
            base_po=order.base_po,
            customers=order.customers,
            styles=order.styles,
            product_types=", ".join(order.product_groups),
            cm_price=as_float(order.cm_price),
            output=float(order.output),
            smv=as_float(order.smv),
            efficiency=as_float(order.efficiency),
            first_day=order.first_day,
            matches=order.matches,
        )
        for order in orders
    ]


def strength_dtos(strengths: list[LineStrength]) -> list[LineStrengthDTO]:
    """Sorted by factory (fixed order), then line number."""
    factories = list(Factory)
    ordered = sorted(strengths, key=lambda item: (factories.index(item.factory), line_sort_key(item.line)))
    return [
        LineStrengthDTO(
            factory=item.factory.value,
            line=item.line,
            strong_groups=list(item.strong_groups),
            buyers=item.buyers,
            changeover_speed=item.changeover_speed,
            remark=item.remark,
            file_name=item.file_name,
            updated_at=item.updated_at,
        )
        for item in ordered
    ]


class LineTrendResponseBuilder(BaseBuilder[LineDetailResponse]):
    """BR-90 (thêm 2026-11-13 lần 2) the answer to a `trend_line` request: only the periods of that line."""

    def __init__(self, points: list[LineTrendPoint]) -> None:
        self.points = points

    def build(self) -> LineDetailResponse:
        return LineDetailResponse(
            rows=[],
            factory_days=[],
            has_data=bool(self.points),
            trend=[
                LineTrendPointDTO(
                    period=point.period.label,
                    start=point.period.from_date,
                    output=as_float(point.output),
                    efficiency=as_float(point.efficiency),
                    mo8h=as_float(point.mo8h),
                    efficiency_below=is_below(point.efficiency_assessment),
                    mo8h_below=is_below(point.mo8h_assessment),
                )
                for point in self.points
            ],
        )

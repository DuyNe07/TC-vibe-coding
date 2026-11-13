"""UC-31: the rows of Screen 6 Line performance -> response DTO."""

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.builders.display import as_float, is_below
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverResponse, LinePerformanceDTO
from backend.features.sewing_productivity.models.report_values import LinePerformance


class LinePerformanceResponseBuilder(BaseBuilder[ChangeoverResponse]):
    def __init__(self, rows: list[LinePerformance]) -> None:
        self.rows = rows

    def build(self) -> ChangeoverResponse:
        return ChangeoverResponse(
            has_data=bool(self.rows),
            line_performance=[
                LinePerformanceDTO(
                    line=row.line,
                    is_total=row.is_total,
                    operators=as_float(row.operators),
                    target_output=as_float(row.target_output),
                    output=as_float(row.output),
                    output_ratio=as_float(row.output_ratio),
                    target_value=as_float(row.target_value),
                    value=as_float(row.value),
                    value_ratio=as_float(row.value_ratio),
                    mo8h=as_float(row.mo8h),
                    output_ratio_below=is_below(row.output_ratio_assessment),
                    mo8h_below=is_below(row.mo8h_assessment),
                )
                for row in self.rows
            ],
        )

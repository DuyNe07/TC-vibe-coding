"""UC-21 / UC-23 / UC-24: calculation preview (and saved yarn) → PricingResultResponse."""

from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.yarn_costing.builders.dto_builders import component_dto, line_dto, stage_cost_dto, yarn_dto
from backend.features.yarn_costing.constants import STORAGE_QUANTUM
from backend.features.yarn_costing.dto.pricing_dto import PricingResultResponse
from backend.features.yarn_costing.models.costing import PricingPreview
from backend.features.yarn_costing.models.enums import LineType
from backend.features.yarn_costing.models.yarn import PriceLine, Yarn


class PricingResultBuilder(BaseBuilder[PricingResultResponse]):
    def __init__(
        self, preview: PricingPreview, saved: Yarn | None, trial_factor: Decimal, rate: Decimal | None, message: str
    ) -> None:
        self.preview, self.saved, self.trial_factor, self.rate, self.message = (
            preview,
            saved,
            trial_factor,
            rate,
            message,
        )

    def build(self) -> PricingResultResponse:
        yarn = self.saved or self.preview.candidate
        result = self.preview.result
        line = trial = None
        if result.passed:
            if self.saved is not None and self.saved.regular_line is not None:
                regular = self.saved.regular_line
                trial_line = next((x for x in self.saved.lines if x.line_type == LineType.THI_NGHIEM), None)
            else:
                cost = result.cost
                regular = PriceLine(line_code=yarn.yarn_code, line_type=LineType.THUONG, cost=cost)
                trial_cost = cost.scaled(self.trial_factor)
                trial_cost = trial_cost.model_copy(
                    update={k: getattr(trial_cost, k).quantize(STORAGE_QUANTUM) for k in type(trial_cost).model_fields}
                )
                trial_line = PriceLine(line_code=f"{yarn.yarn_code}TN", line_type=LineType.THI_NGHIEM, cost=trial_cost)
            line = line_dto(yarn, regular, self.rate)
            trial = line_dto(yarn, trial_line, self.rate) if trial_line else None
        return PricingResultResponse(
            message=self.message,
            saved=self.saved is not None,
            check_passed=result.passed,
            reasons=result.reasons,
            warning_stages=self.preview.warning_stages,
            reference_yarn_code=self.preview.reference_yarn_code,
            components=[component_dto(c) for c in yarn.components],
            stage_details=[stage_cost_dto(d) for d in result.details],
            line=line,
            trial_line=trial,
            yarn=yarn_dto(yarn, self.rate),
        )

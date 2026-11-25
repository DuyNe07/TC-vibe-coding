"""Screen 2 widgets -> CostsheetInputRequest (pure mapping: no calculation, no validation)."""

from typing import Any

from backend.features.woven_costing.dto.costsheet_dto import CostsheetInputRequest, CostsheetResponse

BLOCKS = (
    "yarn_lines",
    "twist_lines",
    "weaving",
    "hcm_dyeing",
    "tcdn_dyeing",
    "price",
    "parameter_overrides",
)


def build_input_request(
    w: CostsheetResponse, values: dict[str, Any], *, confirm_yarn_prices: bool = False
) -> CostsheetInputRequest:
    """Stored input of the costsheet, overwritten by what is on screen (blocks not drawn keep their stored values)."""
    data = w.input.model_dump()
    data.update(values.get("order") or {})
    for block in BLOCKS:
        if values.get(block) is not None:
            data[block] = values[block]
    return CostsheetInputRequest(costsheet_id=w.id, confirm_yarn_prices=confirm_yarn_prices, **data)

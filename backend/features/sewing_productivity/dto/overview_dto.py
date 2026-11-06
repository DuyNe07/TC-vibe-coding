"""UC-04, UC-05: overview table and charts. Efficiencies and shares are percent numbers: 91.8 means 91,8%."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import Factory, RankingMetric

__all__ = [
    "ChartPointDTO",
    "ChartsRequest",
    "ChartsResponse",
    "Factory",
    "FactoryOutputDTO",
    "OverviewMetricDTO",
    "OverviewRequest",
    "OverviewResponse",
    "RankedLineDTO",
    "RankingMetric",
]


class OverviewRequest(BaseRequestDTO):
    """An empty list means no filter; `customer_groups` and `product_groups` apply BR-29 only when not empty."""

    from_date: date
    to_date: date
    factories: list[Factory] = []
    customer_groups: list[str] = []
    product_groups: list[str] = []


class OverviewMetricDTO(BaseDTO):
    """One row: `values` and `below` are keyed by factory name (`Fac 1`...). None is shown as "-".

    `below` is the BR-28 result; `decimals` and `suffix` are the BR-50 format of the row."""

    metric: str
    decimals: int
    suffix: str = ""
    values: dict[str, float | None]
    below: dict[str, bool]


class OverviewResponse(BaseResponseDTO):
    metrics: list[OverviewMetricDTO]
    note: str = ""
    has_data: bool


class ChartsRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factories: list[Factory] = []
    customer_groups: list[str] = []
    product_groups: list[str] = []
    ranking_metric: RankingMetric = RankingMetric.EFFICIENCY_B


class ChartPointDTO(BaseDTO):
    day: date
    factory: str
    value: float


class FactoryOutputDTO(BaseDTO):
    factory: str
    output: float
    target_a: float | None = None


class RankedLineDTO(BaseDTO):
    factory: str
    line: str
    value: float


class ChartsResponse(BaseResponseDTO):
    """Days with "-" are left out of the series. `not_applicable_message` is set under a customer or product filter."""

    efficiency_a: list[ChartPointDTO]
    efficiency_b: list[ChartPointDTO]
    mo8h: list[ChartPointDTO]
    output_vs_target: list[FactoryOutputDTO]
    top_lines: list[RankedLineDTO]
    bottom_lines: list[RankedLineDTO]
    not_applicable_message: str = ""
    has_data: bool
    efficiency_no_ratio: list[ChartPointDTO] = []  # BR-55
    # BR-51: the HCM line and bar, apart from the factories; empty when the HCM column is not shown
    hcm_efficiency_a: list[ChartPointDTO] = []
    hcm_efficiency_b: list[ChartPointDTO] = []
    hcm_efficiency_no_ratio: list[ChartPointDTO] = []
    hcm_mo8h: list[ChartPointDTO] = []
    hcm_output: FactoryOutputDTO | None = None

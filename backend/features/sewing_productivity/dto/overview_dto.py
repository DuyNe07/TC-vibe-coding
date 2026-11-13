"""UC-04, UC-05: overview table and charts. Efficiencies and shares are percent numbers: 91.8 means 91,8%."""

from datetime import date

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.sewing_productivity.models.enums import REPORT_FACTORIES, Factory, RankingMetric

__all__ = [
    "MonthGroupDTO",
    "GroupShareDTO",
    "GroupCmPriceDTO",
    "CustomerOutputDTO",
    "ChartPointDTO",
    "ChartsRequest",
    "ChartsResponse",
    "Factory",
    "REPORT_FACTORIES",
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
    cards: list[OverviewMetricDTO] = []  # BR-58: figures shown only on the cards (BR-65, BR-66), not in the table
    note: str = ""
    has_data: bool


class ChartsRequest(BaseRequestDTO):
    from_date: date
    to_date: date
    factories: list[Factory] = []
    customer_groups: list[str] = []
    product_groups: list[str] = []
    ranking_metric: RankingMetric = RankingMetric.EFFICIENCY_B
    products: bool = False  # BR-93 to BR-96 (thêm 2026-11-13 lần 4): also the "Products & customers" figures


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


class GroupShareDTO(BaseDTO):
    """BR-93 `column` = factory name or "Total"; `share` in %."""

    column: str
    group: str
    output: float
    share: float | None = None


class CustomerOutputDTO(BaseDTO):
    """BR-94 one customer group in one factory."""

    customer: str
    factory: str
    output: float


class GroupCmPriceDTO(BaseDTO):
    """BR-95"""

    group: str
    output: float
    cm_price: float


class MonthGroupDTO(BaseDTO):
    """BR-96"""

    month: str
    start: date
    group: str
    output: float


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
    # BR-93 to BR-96 (thêm 2026-11-13 lần 4): only when the request asks for `products`
    product_shares: list[GroupShareDTO] = []  # the chart: 5 groups + Other per column
    product_table: list[GroupShareDTO] = []  # every group per column
    top_customers: list[CustomerOutputDTO] = []
    cm_by_group: list[GroupCmPriceDTO] = []
    monthly_mix: list[MonthGroupDTO] = []
    hcm_output: FactoryOutputDTO | None = None

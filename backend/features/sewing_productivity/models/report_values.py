"""Results of the report calculations. Exact Decimal values: rounding happens only when shown or exported (BR-50)."""

from datetime import date
from decimal import Decimal
from typing import Any

from backend.core.base import BaseValueObject
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.enums import Assessment, Factory, NumberKind, RowType
from backend.features.sewing_productivity.models.settings_records import FactoryGoal, WeeklyChangeover
from backend.features.sewing_productivity.models.source_records import TargetRecord


class ReportFacts(BaseValueObject):
    """The rows of one report, narrowed to its period, with the lookups every calculation needs.

    Built with ``model_construct`` (32 000 rows): ``rows`` ignores the customer and product filters, ``shown`` applies
    them (BR-29). Keys of the lookups: ``(factory, line, day)`` or ``(factory, day)``."""

    from_date: date
    to_date: date
    factories: tuple[Factory, ...]
    filtered: bool = False
    rows: dict[Factory, list[CleanRow]] = {}
    shown: dict[Factory, list[CleanRow]] = {}
    targets: dict[Factory, list[TargetRecord]] = {}
    target_map: dict[Any, Decimal] = {}
    line_hours: dict[Any, Decimal] = {}
    line_sewers: dict[Any, Decimal] = {}
    factory_hours: dict[Any, Decimal] = {}
    workers: dict[Any, Decimal] = {}
    headcount: dict[Any, Decimal] = {}  # BR-65 total headcount, only the days that have it
    goals: dict[Factory, list[FactoryGoal]] = {}
    weekly: list[WeeklyChangeover] = []
    # BR-86 (thêm 2026-11-13) the strong item groups of each (factory, line), case folded
    strengths: dict[Any, frozenset[str]] = {}
    # BR-87 (thêm 2026-11-13) each (factory, line): its working days with the codes it ran, over the whole history;
    # empty when the report does not count changeovers
    code_days: dict[Any, list[tuple[date, frozenset[Any]]]] = {}


class LineStat(BaseValueObject):
    """One line on one day (DAY), over the whole period (PERIOD), or the factory total (TOTAL)."""

    row_type: RowType
    factory: Factory
    line: str
    day: date | None = None
    target_a: Decimal | None = None
    output: Decimal = Decimal(0)
    efficiency_a: Decimal | None = None
    target_b: Decimal | None = None
    efficiency_b: Decimal | None = None
    target_no_ratio: Decimal | None = None
    efficiency_no_ratio: Decimal | None = None
    cm_earning: Decimal = Decimal(0)
    sewers: Decimal | None = None
    hours: Decimal | None = None
    mo: Decimal | None = None
    mo8h: Decimal | None = None
    mismatched_output: Decimal = Decimal(0)
    efficiency_a_assessment: Assessment = Assessment.NOT_AVAILABLE
    efficiency_b_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE


class FactoryDayStat(BaseValueObject):
    """One factory (or the HCM group: BR-51) on one day; ``day`` is None on the total row (BR-48)."""

    factory: Factory | None = None
    group_name: str = ""
    day: date | None = None
    mo: Decimal | None = None
    hours: Decimal | None = None
    mo8h: Decimal | None = None
    target_a: Decimal | None = None
    efficiency_a: Decimal | None = None
    target_b: Decimal | None = None
    output: Decimal = Decimal(0)
    efficiency_b: Decimal | None = None
    target_no_ratio: Decimal | None = None
    efficiency_no_ratio: Decimal | None = None
    cm_earning: Decimal = Decimal(0)
    workers: Decimal | None = None
    efficiency_b_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE

    @property
    def column(self) -> str:
        return self.factory.value if self.factory else self.group_name


class FactorySummary(BaseValueObject):
    """One column of the overview table (Screen 1): one factory, or the HCM group (BR-51)."""

    factory: Factory | None = None
    group_name: str = ""
    target_a: Decimal | None = None
    output: Decimal | None = None
    efficiency_target: Decimal | None = None
    efficiency_a: Decimal | None = None
    efficiency_a_vs_target: Decimal | None = None
    target_b: Decimal | None = None
    efficiency_b: Decimal | None = None
    efficiency_b_vs_target: Decimal | None = None
    target_no_ratio: Decimal | None = None
    efficiency_no_ratio: Decimal | None = None
    cm_earning: Decimal | None = None
    mo8h_target: Decimal | None = None
    mo8h: Decimal | None = None
    mo8h_vs_target: Decimal | None = None
    average_cm_price: Decimal | None = None
    average_hours: Decimal | None = None
    strength_match: Decimal | None = None
    weekly_changeover: Decimal | None = None
    weekly_changeover_per_line: Decimal | None = None
    average_smv: Decimal | None = None  # BR-66, cards and Screen 4
    direct_labor: Decimal | None = None  # BR-65, cards only
    direct_workers: Decimal | None = None  # BR-69 Direct worker, Screen 4 only
    changeovers: int | None = None  # BR-87, Screen 4 only (thêm 2026-11-13)
    changeover_per_line_day: Decimal | None = None  # BR-89, Screen 4 only (thêm 2026-11-13)
    efficiency_a_assessment: Assessment = Assessment.NOT_AVAILABLE
    efficiency_b_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE

    @property
    def column(self) -> str:
        return self.factory.value if self.factory else self.group_name


class DailyFactorySummary(BaseValueObject):
    """One column of the daily report (Screen 3): one factory, or the HCM group (BR-51)."""

    factory: Factory | None = None
    group_name: str = ""
    mo: Decimal | None = None
    hours: Decimal | None = None
    target_mo8h: Decimal | None = None
    mo8h: Decimal | None = None
    mo8h_vs_target: Decimal | None = None
    target_output: Decimal | None = None
    output: Decimal | None = None
    efficiency_a: Decimal | None = None
    efficiency_b: Decimal | None = None
    efficiency_no_ratio: Decimal | None = None
    strength_match: Decimal | None = None
    workers: Decimal | None = None
    efficiency_a_assessment: Assessment = Assessment.NOT_AVAILABLE
    efficiency_b_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE

    @property
    def column(self) -> str:
        return self.factory.value if self.factory else self.group_name


class FactoryDetail(BaseValueObject):
    """BR-64 what one `<factory>-detailed` sheet needs: line rows (DAY and PERIOD), the factory days, its summary."""

    factory: Factory
    lines: list[LineStat]
    days: list[FactoryDayStat]
    summary: FactorySummary


class RankedLine(BaseValueObject):
    factory: Factory
    line: str
    value: Decimal


class MatrixCell(BaseValueObject):
    value: Decimal | None = None
    assessment: Assessment | None = None


class MatrixRow(BaseValueObject):
    line: str
    is_total: bool = False
    cells: dict[date, MatrixCell] = {}
    period: MatrixCell = MatrixCell()


class MatrixTable(BaseValueObject):
    """One table of Screen 5: lines in rows, days in columns."""

    title: str
    sheet: str
    kind: NumberKind
    rows: list[MatrixRow] = []


class ChangeoverCount(BaseValueObject):
    """BR-32 to BR-36 for one factory (and one month in the monthly table)."""

    factory: Factory
    month: str = ""
    kpi_count: int = 0
    working_days: int = 0
    line_count: int = 0
    kpi: Decimal | None = None
    rerun_count: int = 0
    weekly_count: int | None = None


class ChangeoverLineCount(BaseValueObject):
    factory: Factory
    line: str
    kpi_count: int = 0
    rerun_count: int = 0


class ChangeoverDetail(BaseValueObject):
    day: date
    factory: Factory
    line: str
    base_po: str
    style: str
    smv: Decimal
    cm_price: Decimal


class ChangeoverReport(BaseValueObject):
    has_data: bool = False
    total_kpi_count: int = 0
    total_rerun_count: int = 0
    by_factory: list[ChangeoverCount] = []
    by_month: list[ChangeoverCount] = []
    by_line: list[ChangeoverLineCount] = []
    details: list[ChangeoverDetail] = []


class PeriodRange(BaseValueObject):
    """BR-68 one period of Screen 4: its name and the chosen days it covers."""

    label: str
    from_date: date
    to_date: date


class PeriodSummaries(BaseValueObject):
    """UC-29 one period with one summary per chosen factory, then HCM (when shown) and Total."""

    period: PeriodRange
    summaries: list[FactorySummary]


class LineOverview(BaseValueObject):
    """UC-06 (sửa 2026-11-12) one row of the Line Detail table (BR-83), or its Total row."""

    line: str
    is_total: bool = False
    output: Decimal | None = None
    efficiency: Decimal | None = None  # %Efficiency (with ratio) = BR-19 (thêm 2026-11-13)
    mo8h: Decimal | None = None
    hours: Decimal | None = None
    matching_ratio: Decimal | None = None  # BR-86 (sửa 2026-11-13)
    changeover: int = 0  # BR-87 (sửa 2026-11-13)
    efficiency_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE


class LineOrder(BaseValueObject):
    """UC-06 (sửa 2026-11-12) one base order a line made in the chosen dates (BR-84). `matches` None = "-"."""

    line: str
    base_po: str
    customers: str
    styles: str
    product_groups: list[str]
    cm_price: Decimal | None = None
    output: Decimal
    smv: Decimal | None = None  # BR-88 (thêm 2026-11-13)
    efficiency: Decimal | None = None  # BR-88 (thêm 2026-11-13)
    first_day: date | None = None
    matches: bool | None = None


class LineTrendPoint(BaseValueObject):
    """BR-90 (thêm 2026-11-13 lần 2) one period of the "Line trend" of one line, figures as the Line Detail table."""

    period: PeriodRange
    output: Decimal | None = None
    efficiency: Decimal | None = None
    mo8h: Decimal | None = None
    efficiency_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE


class LinePerformance(BaseValueObject):
    """UC-31 one row of Screen 6 (BR-78), or its Total row (BR-79), with the BR-80 assessments."""

    line: str
    is_total: bool = False
    operators: Decimal | None = None
    target_output: Decimal | None = None
    output: Decimal | None = None
    output_ratio: Decimal | None = None
    target_value: Decimal | None = None
    value: Decimal | None = None
    value_ratio: Decimal | None = None
    mo8h: Decimal | None = None
    output_ratio_assessment: Assessment = Assessment.NOT_AVAILABLE
    mo8h_assessment: Assessment = Assessment.NOT_AVAILABLE


class GroupShare(BaseValueObject):
    """BR-93 one product group of one column (a factory or Total): its output and share of the column (%)."""

    column: str
    group: str
    output: Decimal
    share: Decimal | None = None


class CustomerOutput(BaseValueObject):
    """BR-94 the output of one customer group in one factory."""

    customer: str
    factory: Factory
    output: Decimal


class GroupCmPrice(BaseValueObject):
    """BR-95 the average CM price of one product group."""

    group: str
    output: Decimal
    cm_price: Decimal


class MonthGroupOutput(BaseValueObject):
    """BR-96 the output of one product group in one month."""

    month: str
    start: date
    group: str
    output: Decimal


class ProductMix(BaseValueObject):
    """BR-93 to BR-96 everything the "Products & customers" area of Overview shows."""

    shares: list[GroupShare] = []
    table: list[GroupShare] = []
    customers: list[CustomerOutput] = []
    cm_prices: list[GroupCmPrice] = []
    months: list[MonthGroupOutput] = []

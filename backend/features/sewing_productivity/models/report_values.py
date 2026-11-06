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
    goals: dict[Factory, list[FactoryGoal]] = {}
    weekly: list[WeeklyChangeover] = []


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

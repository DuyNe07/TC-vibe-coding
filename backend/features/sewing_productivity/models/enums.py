"""Lists of values of feature "Năng suất xưởng may"."""

from enum import StrEnum


class Factory(StrEnum):
    FAC_1 = "Fac 1"
    FAC_2 = "Fac 2"
    FAC_3 = "Fac 3"
    FAC_5 = "Fac 5"


class Assessment(StrEnum):
    """BR-28 result, written in tables and Excel files."""

    PASSED = "Đạt"
    BELOW = "Dưới ngưỡng"
    NOT_AVAILABLE = "-"


class RankingMetric(StrEnum):
    """BR-44 metric used to rank the lines."""

    EFFICIENCY_B = "Hiệu suất B"
    EFFICIENCY_A = "Hiệu suất A"
    MO8H = "MO 8h"


class RowType(StrEnum):
    """Kind of a report row: one day, the whole period of a line, or the factory total."""

    DAY = "day"
    PERIOD = "period"
    TOTAL = "total"


class NumberKind(StrEnum):
    """BR-50 display format of a number."""

    INTEGER = "integer"
    PERCENT = "percent"
    MONEY = "money"
    KPI = "kpi"
    PEOPLE = "people"
